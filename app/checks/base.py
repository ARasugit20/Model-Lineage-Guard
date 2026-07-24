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


def entity_type_index(context: dict[str, Any]) -> dict[str, list[str]]:
    """Return a scan-local entity type index keyed by DataHub entity type."""
    cached = context.get("_mlguard_entity_type_index")
    if isinstance(cached, dict):
        return cached

    index: dict[str, list[str]] = {}
    for urn, entity in lineage_entities(context).items():
        entity_type = _entity_type(urn, entity)
        index.setdefault(entity_type, []).append(urn)
    context["_mlguard_entity_type_index"] = index
    return index


def lineage_entities_by_type(
    context: dict[str, Any],
    *entity_types: str,
) -> dict[str, dict[str, Any]]:
    """Return entity metadata filtered through the scan-local type index."""
    entities = lineage_entities(context)
    index = entity_type_index(context)
    urns = [urn for entity_type in entity_types for urn in index.get(entity_type, [])]
    return {urn: entities[urn] for urn in urns if urn in entities}


def _entity_type(urn: str, entity: dict[str, Any]) -> str:
    explicit_type = entity.get("type")
    if explicit_type:
        return str(explicit_type)
    if urn.startswith("urn:li:"):
        return urn.split(":", maxsplit=3)[2]
    for entity_type, aspect_name in (
        ("dataset", "dataset"),
        ("mlModel", "model"),
        ("mlModelDeployment", "deployment"),
    ):
        if entity.get(aspect_name):
            return entity_type
    return "unknown"


def contains_token(value: Any, *tokens: str) -> bool:
    """Return whether a value's string form contains any token, case-insensitively."""
    lowered = str(value).lower()
    return any(token.lower() in lowered for token in tokens)
