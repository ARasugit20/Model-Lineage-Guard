"""Shared protocol for lineage risk checks."""

from typing import Any, Protocol

from app.findings import Finding


class Check(Protocol):
    """Risk check interface implemented by every check module."""

    name: str
    severity: str

    def run(self, context: dict[str, Any]) -> list[Finding]:
        """Return findings discovered in the supplied scan context."""


def entity_properties(entity: dict[str, Any]) -> dict[str, str]:
    """Return merged custom properties across supported DataHub aspect shapes."""
    properties: dict[str, str] = {}
    for aspect_name in ("dataset", "model", "deployment"):
        aspect = entity.get(aspect_name) or {}
        custom = aspect.get("customProperties") or {}
        properties.update({str(key): str(value) for key, value in custom.items()})
    return properties


def lineage_entities(context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return entity metadata from a scan context."""
    entities = context.get("entities", {})
    return entities if isinstance(entities, dict) else {}


def contains_token(value: Any, *tokens: str) -> bool:
    """Return whether a value's string form contains any token, case-insensitively."""
    lowered = str(value).lower()
    return any(token.lower() in lowered for token in tokens)
