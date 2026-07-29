"""File-based subprocess adapters for ProofBridge and ProofFlow."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import tempfile
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError

from proof_faithfulness.models.base import (
    AdapterConfigurationError,
    AdapterResponseError,
    AdapterResult,
    AdapterTransportError,
    ModelCapabilities,
    ModelInput,
    validate_request_identity,
    validate_sampling_recipe,
)
from proof_faithfulness.models.config import (
    PipelineAdapterConfig,
    compute_adapter_config_hash,
)
from proof_faithfulness.models.openai_compat import compute_usd_cost
from proof_faithfulness.schema import TokenUsage

PIPELINE_GIT_TIMEOUT_SECONDS = 60


class PipelineResponse(BaseModel):
    """Strict response file emitted by a pipeline integration shim."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)

    text: str
    provider_request_id: str | None = None
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    usd_cost: Decimal | None = Field(default=None, ge=0)
    finish_reason: str | None = None
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class JsonSubprocessAdapter:
    """Runs an external prover pipeline using request/response JSON files."""

    def __init__(self, config: PipelineAdapterConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return self._config.adapter

    @property
    def capabilities(self) -> ModelCapabilities:
        return self._config.capabilities

    def generate(self, model_input: ModelInput) -> AdapterResult:
        self._verify_pipeline_commit()
        validate_request_identity(
            model_input,
            adapter_name=self.name,
            provider=self._config.provider,
            model_key=self._config.model_key,
            model_id=self._config.model_id,
            model_revision=self._config.model_revision,
            backend_config_hash=compute_adapter_config_hash(self._config),
            capabilities=self.capabilities,
        )
        validate_sampling_recipe(
            model_input,
            temperature=self._config.model.decoding.temperature,
            top_p=self._config.model.decoding.top_p,
            max_tokens=self._config.model.decoding.max_tokens,
            seed_base=self._config.model.decoding.seed_base,
            extra=self._config.model.decoding.extra,
        )
        scratch_dir = self._config.scratch_dir
        if scratch_dir is not None:
            scratch_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch_dir) as temporary_directory:
            directory = Path(temporary_directory)
            request_path = directory / "request.json"
            response_path = directory / "response.json"
            request_payload = {
                "schema_version": "1.0",
                "pipeline": self.name,
                "model_key": self._config.model_key,
                "model_id": self._config.model_id,
                "model_revision": self._config.model_revision,
                "generation_request": model_input.request.model_dump(mode="json"),
                "messages": [message.model_dump(mode="json") for message in model_input.messages],
            }
            request_path.write_text(
                json.dumps(request_payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            command = [
                token.replace("{request_path}", str(request_path)).replace(
                    "{response_path}", str(response_path)
                )
                for token in self._config.command
            ]
            stdout_path = directory / "stdout.log"
            stderr_path = directory / "stderr.log"
            try:
                with (
                    stdout_path.open("wb") as stdout_file,
                    stderr_path.open("wb") as stderr_file,
                ):
                    process = subprocess.Popen(
                        command,
                        cwd=self._config.workdir,
                        env=self._environment(),
                        start_new_session=True,
                        stdin=subprocess.DEVNULL,
                        stdout=stdout_file,
                        stderr=stderr_file,
                    )
            except OSError as error:
                raise AdapterTransportError(
                    f"Unable to start {self.name} pipeline: {type(error).__name__}"
                ) from error
            timed_out = False
            try:
                process.wait(timeout=self._config.timeout_seconds)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                timed_out = True
                return_code = None
            finally:
                _terminate_process_group(process)
            stdout = _read_bounded_bytes(
                stdout_path,
                max_bytes=self._config.max_response_bytes,
            )
            stderr = _read_bounded_bytes(
                stderr_path,
                max_bytes=self._config.max_response_bytes,
            )
            if timed_out:
                raise AdapterTransportError(
                    f"{self.name} pipeline timed out after {self._config.timeout_seconds}s"
                )
            if return_code != 0:
                diagnostics, truncated = _bounded_process_diagnostics(
                    stdout,
                    stderr,
                    max_bytes=self._config.max_response_bytes,
                )
                raise AdapterResponseError(
                    f"{self.name} pipeline exited with status {return_code}",
                    raw_response=diagnostics,
                    raw_truncated=truncated,
                )
            if not response_path.is_file():
                raise AdapterResponseError(f"{self.name} pipeline did not write response.json")
            raw_response = _read_limited_file(
                response_path,
                max_bytes=self._config.max_response_bytes,
                pipeline_name=self.name,
            )
            try:
                parsed = PipelineResponse.model_validate_json(raw_response)
            except ValidationError as error:
                raise AdapterResponseError(
                    f"{self.name} pipeline returned invalid response JSON",
                    raw_response=raw_response,
                ) from error

        usage = TokenUsage(
            input_tokens=parsed.input_tokens,
            output_tokens=parsed.output_tokens,
        )
        usd_cost = compute_usd_cost(usage, self._config.model.pricing_usd_per_mtok)
        if parsed.usd_cost is not None and parsed.usd_cost != usd_cost:
            raise AdapterResponseError(
                "Pipeline-reported cost does not match pinned pricing",
                raw_response=raw_response,
                provider_request_id=parsed.provider_request_id,
            )
        return AdapterResult(
            request_id=model_input.request.request_id,
            text=parsed.text,
            raw_response=raw_response,
            provider_request_id=parsed.provider_request_id,
            token_usage=usage,
            usd_cost=usd_cost,
            finish_reason=parsed.finish_reason,
        )

    def _environment(self) -> dict[str, str]:
        missing = [name for name in self._config.environment_names if name not in os.environ]
        if missing:
            raise AdapterConfigurationError(
                f"Required pipeline environment variables are unset: {sorted(missing)}"
            )
        return {name: os.environ[name] for name in self._config.environment_names}

    def _verify_pipeline_commit(self) -> None:
        expected = self._config.model.pipeline_commit
        if expected is None:
            raise AdapterConfigurationError(
                f"Pipeline commit is not frozen for {self._config.model.key}"
            )
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self._config.workdir,
                capture_output=True,
                check=False,
                text=True,
                timeout=PIPELINE_GIT_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise AdapterConfigurationError("Unable to inspect pipeline Git commit") from error
        actual = result.stdout.strip()
        if result.returncode != 0 or actual != expected:
            raise AdapterConfigurationError(
                f"Pipeline checkout does not match pinned commit for {self._config.model.key}"
            )
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=self._config.workdir,
                capture_output=True,
                check=False,
                text=True,
                timeout=PIPELINE_GIT_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise AdapterConfigurationError("Unable to inspect pipeline Git status") from error
        if status.returncode != 0 or status.stdout:
            raise AdapterConfigurationError(
                f"Pipeline checkout is not clean for {self._config.model.key}"
            )


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    """Immediately terminate a completed or timed-out pipeline process group."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        if process.poll() is None:
            process.wait()
        return
    if process.poll() is None:
        process.wait()


def _read_limited_file(path: Path, *, max_bytes: int, pipeline_name: str) -> bytes:
    with path.open("rb") as response_file:
        content = response_file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise AdapterResponseError(
            f"{pipeline_name} response exceeds {max_bytes} byte limit",
            raw_response=content,
            raw_truncated=True,
        )
    return content


def _bounded_process_diagnostics(
    stdout: bytes,
    stderr: bytes,
    *,
    max_bytes: int,
) -> tuple[bytes, bool]:
    payload = json.dumps(
        {
            "schema_version": "1.0",
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        },
        ensure_ascii=True,
        sort_keys=True,
    ).encode("utf-8")
    if len(payload) <= max_bytes:
        return payload, False
    return payload[:max_bytes], True


def _read_bounded_bytes(path: Path, *, max_bytes: int) -> bytes:
    with path.open("rb") as stream:
        return stream.read(max_bytes + 1)


class ProofBridgeAdapter(JsonSubprocessAdapter):
    def __init__(self, config: PipelineAdapterConfig) -> None:
        if config.adapter != "proofbridge":
            raise ValueError("ProofBridgeAdapter requires adapter=proofbridge")
        super().__init__(config)


class ProofFlowAdapter(JsonSubprocessAdapter):
    def __init__(self, config: PipelineAdapterConfig) -> None:
        if config.adapter != "proofflow":
            raise ValueError("ProofFlowAdapter requires adapter=proofflow")
        super().__init__(config)
