"""Adapt a harness request to the pinned upstream ProofFlow orchestration."""

from __future__ import annotations

import argparse
import copy
import json
import os
import time
from pathlib import Path
from typing import Any

from proofflow import LeanServer, LLMManager, ProofFlow

PROOFFLOW_ROOT = Path("/gscratch/scrubbed/thuang27/proof-faithfulness/pipelines/ProofFlow")


class RecordedLLMManager(LLMManager):
    """Use ProofFlow prompts while retaining exact decoded API responses and usage."""

    def __init__(self, *, sampling: dict[str, Any], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._sampling = sampling
        self.input_tokens = 0
        self.output_tokens = 0

    def call_llm(
        self,
        messages: list[dict[str, str]],
        logs: list[dict[str, Any]] | None = None,
        max_new_tokens: int = 16384,
        temperature: float = 0.9,
    ) -> tuple[str, list[dict[str, str]]]:
        del max_new_tokens, temperature
        if self.client is None:
            raise RuntimeError("ProofFlow compatibility requires its remote-client path")
        sent_messages = copy.deepcopy(messages)
        if self.system_prompt and (
            not sent_messages or sent_messages[0].get("role") != "system"
        ):
            sent_messages.insert(0, {"role": "system", "content": self.system_prompt})
        started = time.time()
        completion = self.client.chat.completions.create(
            model=self.model_info["model"],
            messages=sent_messages,
            temperature=self._sampling["temperature"],
            top_p=self._sampling["top_p"],
            max_tokens=self._sampling["max_tokens"],
            seed=self._sampling["seed"],
        )
        if not completion.choices or not completion.choices[0].message.content:
            raise RuntimeError("ProofFlow received an empty OpenAI-compatible response")
        text = completion.choices[0].message.content
        finished = time.time()
        usage = completion.usage
        if usage is not None:
            self.input_tokens += usage.prompt_tokens
            self.output_tokens += usage.completion_tokens
        updated = [*sent_messages, {"role": "assistant", "content": text}]
        if logs is not None:
            logs.append(
                {
                    "start_time": started,
                    "end_time": finished,
                    "duration": finished - started,
                    "model": self.model_info["model"],
                    "messages": updated,
                    "raw_response": completion.model_dump(mode="json"),
                    "success": True,
                }
            )
        return text, updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    args = parser.parse_args()

    request = json.loads(args.request.read_text(encoding="utf-8"))
    if request.get("pipeline") != "proofflow" or not request.get("messages"):
        raise ValueError("ProofFlow shim received an invalid harness request")
    generation = request["generation_request"]
    sampling = generation["sampling"]
    model_info = {
        "api_key": "calibration-local",
        "base_url": os.environ["PF_PROOFFLOW_BASE_URL"],
        "model": os.environ["PF_PROOFFLOW_MODEL_ID"],
    }

    def manager(prompt_name: str) -> RecordedLLMManager:
        return RecordedLLMManager(
            sampling=sampling,
            model_info=model_info,
            system_prompt_path=str(PROOFFLOW_ROOT / "prompts" / prompt_name),
        )

    graph = manager("proof_graph.md")
    formalizer = manager("lemma_formalizer.md")
    solver = manager("lemma_prover.md")
    flow = ProofFlow(
        lean_server=LeanServer(project_path=os.environ["PF_PROOFFLOW_LEAN_PROJECT"]),
        graph_model_manager=graph,
        formalize_model_manager=formalizer,
        solver_model_manager=solver,
        verbose=False,
    )
    supplied_text = "\n\n".join(message["content"] for message in request["messages"])
    flow.autoformalize_series(
        supplied_text,
        graph_builder_retries=1,
        formalizer_retries=1,
        prover_retries=1,
    )
    logs = flow.get_llm_call_logs()
    response = {
        "text": flow.get_lean_code(),
        "provider_request_id": f"proofflow-{generation['request_id']}",
        "input_tokens": sum(item.input_tokens for item in (graph, formalizer, solver)),
        "output_tokens": sum(item.output_tokens for item in (graph, formalizer, solver)),
        "usd_cost": 0,
        "finish_reason": "pipeline_complete",
        "metadata": {
            "upstream_llm_calls": logs,
            "upstream_call_count": len(logs),
        },
    }
    args.response.write_text(
        json.dumps(response, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
