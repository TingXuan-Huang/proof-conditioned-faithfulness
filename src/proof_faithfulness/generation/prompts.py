"""Versioned prompt loading and literal double-brace rendering."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from proof_faithfulness.models import ChatMessage

_PLACEHOLDER = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")


@dataclass(frozen=True)
class PromptTemplate:
    """One versioned prompt template and its raw-byte identity."""

    name: str
    raw: bytes
    text: str
    sha256: str

    def render(self, variables: Mapping[str, str]) -> str:
        """Renders exact placeholders without evaluating template code."""
        template_skeleton = _PLACEHOLDER.sub("", self.text)
        if "{{" in template_skeleton or "}}" in template_skeleton:
            raise ValueError(f"Malformed or unsupported placeholder in {self.name}")
        required = set(_PLACEHOLDER.findall(self.text))
        missing = required - set(variables)
        if missing:
            raise ValueError(f"Missing template variables for {self.name}: {sorted(missing)}")

        def replace(match: re.Match[str]) -> str:
            return variables[match.group(1)]

        return _PLACEHOLDER.sub(replace, self.text)


class PromptRepository:
    """Loads templates from one fixed directory and hashes their raw bytes."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def load(self, name: str) -> PromptTemplate:
        """Loads a plain ``.txt`` basename without allowing path traversal."""
        relative = Path(name)
        if relative.name != name or relative.suffix != ".txt":
            raise ValueError(f"Prompt template must be a .txt basename: {name!r}")
        path = self._root / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Prompt template must be a regular file: {name}")
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"Prompt template is not UTF-8: {name}") from error
        return PromptTemplate(
            name=name,
            raw=raw,
            text=text,
            sha256=hashlib.sha256(raw).hexdigest(),
        )


def render_messages(
    *,
    repository: PromptRepository,
    system_template: str,
    user_template: str,
    variables: Mapping[str, str],
) -> tuple[tuple[ChatMessage, ChatMessage], PromptTemplate]:
    """Renders the configured system and user templates as two chat messages."""
    system = repository.load(system_template)
    user = repository.load(user_template)
    messages = (
        ChatMessage(role="system", content=system.render(variables)),
        ChatMessage(role="user", content=user.render(variables)),
    )
    return messages, user


def template_name_and_version(filename: str) -> tuple[str, str]:
    """Parses names such as ``preservation_v1.txt`` into identity fields."""
    stem = Path(filename).stem
    name, separator, version_number = stem.rpartition("_v")
    if not separator or not name or not version_number.isdigit():
        raise ValueError(f"Prompt filename must end in _v<number>.txt: {filename}")
    return name, f"v{version_number}"
