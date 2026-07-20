"""Thin DataHub client wrapper for Agent Context Kit and SDK calls."""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal, TypeVar

from datahub.ingestion.graph.client import DatahubClientConfig, DataHubGraph
from datahub.ingestion.graph.openapi import RelationshipDirection
from datahub.metadata.schema_classes import (
    DatasetPropertiesClass,
    GlobalTagsClass,
    GlossaryTermsClass,
    MLModelDeploymentPropertiesClass,
    MLModelPropertiesClass,
    OwnershipClass,
    SchemaMetadataClass,
    UpstreamLineageClass,
)
from datahub.sdk.main_client import DataHubClient as AgentDataHubClient
from datahub_agent_context import DataHubContext

Direction = Literal["upstream", "downstream"]
T = TypeVar("T")
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DataHubSettings:
    """Connection settings for a DataHub GMS endpoint."""

    gms_host: str
    token: str | None = None
    timeout_seconds: float = 15.0
    retry_attempts: int = 3
    retry_backoff_seconds: float = 0.25

    @classmethod
    def from_env(cls) -> DataHubSettings:
        """Create settings from DATAHUB_GMS_HOST and DATAHUB_TOKEN."""
        host = os.getenv("DATAHUB_GMS_HOST", "http://localhost:8080")
        token = os.getenv("DATAHUB_TOKEN") or None
        return cls(gms_host=host, token=token)


class DataHubClient:
    """Read DataHub metadata through Agent Context Kit with SDK graph fallbacks."""

    def __init__(self, settings: DataHubSettings | None = None) -> None:
        self.settings = settings or DataHubSettings.from_env()
        config = DatahubClientConfig(
            server=self.settings.gms_host,
            token=self.settings.token,
            timeout_sec=self.settings.timeout_seconds,
        )
        self.graph = DataHubGraph(config)
        self.agent_client = AgentDataHubClient(graph=self.graph)
        self.context = DataHubContext(self.agent_client)

    def test_connection(self) -> bool:
        """Return whether the configured DataHub instance is reachable."""
        self._call_with_retry(self.graph.test_connection)
        return True

    def get_dataset(self, urn: str) -> dict[str, Any]:
        """Return dataset-level properties for a DataHub dataset URN."""
        properties = self._call_with_retry(self.graph.get_aspect, urn, DatasetPropertiesClass)
        return self._aspect_to_dict(properties)

    def get_model(self, urn: str) -> dict[str, Any]:
        """Return ML model properties for a DataHub ML model URN."""
        properties = self._call_with_retry(self.graph.get_aspect, urn, MLModelPropertiesClass)
        return self._aspect_to_dict(properties)

    def get_deployment(self, urn: str) -> dict[str, Any]:
        """Return ML model deployment properties for a deployment URN."""
        properties = self._call_with_retry(
            self.graph.get_aspect,
            urn,
            MLModelDeploymentPropertiesClass,
        )
        return self._aspect_to_dict(properties)

    def get_lineage(
        self,
        urn: str,
        direction: Direction = "upstream",
        *,
        max_breadth: int = 100,
    ) -> list[dict[str, Any]]:
        """Return direct lineage edges around an entity."""
        relationship_direction = (
            RelationshipDirection.INCOMING
            if direction == "upstream"
            else RelationshipDirection.OUTGOING
        )
        relationships = self._call_with_retry(
            self.graph.get_related_entities,
            entity_urn=urn,
            relationship_types=["DownstreamOf"],
            direction=relationship_direction,
        )
        return [
            {
                "urn": related.urn,
                "type": getattr(related, "type", None),
                "relationship": getattr(related, "relationship", None),
            }
            for index, related in enumerate(relationships)
            if index < max_breadth
        ]

    def get_upstream_lineage(self, urn: str) -> dict[str, Any]:
        """Return the raw upstreamLineage aspect for an entity, if present."""
        lineage = self._call_with_retry(self.graph.get_aspect, urn, UpstreamLineageClass)
        return self._aspect_to_dict(lineage)

    def get_owners(self, urn: str) -> list[str]:
        """Return owner URNs registered on an entity."""
        ownership = self._call_with_retry(self.graph.get_aspect, urn, OwnershipClass)
        if not ownership:
            return []
        return [owner.owner for owner in ownership.owners]

    def get_schema(self, urn: str) -> list[dict[str, Any]]:
        """Return schema fields for a dataset-like entity."""
        schema = self._call_with_retry(self.graph.get_aspect, urn, SchemaMetadataClass)
        return self._schema_fields(schema)

    def _schema_fields(self, schema: SchemaMetadataClass | None) -> list[dict[str, Any]]:
        if not schema:
            return []
        return [
            {
                "fieldPath": field.fieldPath,
                "nativeDataType": field.nativeDataType,
                "description": field.description,
                "nullable": field.nullable,
                "globalTags": self._aspect_to_dict(field.globalTags),
                "glossaryTerms": self._aspect_to_dict(field.glossaryTerms),
            }
            for field in schema.fields
        ]

    def get_glossary_terms(self, urn: str) -> list[str]:
        """Return glossary term URNs directly attached to an entity."""
        terms = self._call_with_retry(self.graph.get_aspect, urn, GlossaryTermsClass)
        if not terms:
            return []
        return [term.urn for term in terms.terms]

    def get_tags(self, urn: str) -> list[str]:
        """Return tag URNs directly attached to an entity."""
        tags = self._call_with_retry(self.graph.get_aspect, urn, GlobalTagsClass)
        if not tags:
            return []
        return [tag.tag for tag in tags.tags]

    def list_ml_models(self) -> list[str]:
        """Return ML model URNs visible to the configured DataHub client."""
        models: list[str] = []
        start = 0
        count = 100
        while True:
            response = self._call_with_retry(
                self.graph.get_search_results,
                entity="mlmodel",
                start=start,
                count=count,
            )
            entities = response.get("entities", [])
            models.extend(entity["entity"] for entity in entities if "entity" in entity)
            if len(entities) < count:
                break
            start += count
        return models

    def scan_context(
        self,
        urn: str,
        *,
        upstream_depth: int = 4,
        downstream_depth: int = 2,
        max_breadth: int = 100,
    ) -> dict[str, Any]:
        """Collect the metadata bundle that later risk checks will consume."""
        upstreams = self._walk_lineage(
            urn,
            "upstream",
            max_depth=upstream_depth,
            max_breadth=max_breadth,
        )
        downstreams = self._walk_lineage(
            urn,
            "downstream",
            max_depth=downstream_depth,
            max_breadth=max_breadth,
        )
        related_urns = [edge["urn"] for edge in upstreams + downstreams if edge.get("urn")]
        related_urns.append(urn)
        unique_urns = sorted(set(related_urns))

        return {
            "target_urn": urn,
            "scan_started_at": datetime.now(UTC).isoformat(),
            "lineage": {
                "upstream": upstreams,
                "downstream": downstreams,
                "raw_upstream_aspect": self.get_upstream_lineage(urn),
            },
            "entities": {
                entity_urn: self.describe_entity(entity_urn) for entity_urn in unique_urns
            },
        }

    def _walk_lineage(
        self,
        urn: str,
        direction: Direction,
        max_depth: int,
        max_breadth: int,
    ) -> list[dict[str, Any]]:
        """Walk lineage edges breadth-first to collect a compact neighborhood."""
        seen: set[str] = {urn}
        frontier = [(urn, 0)]
        edges: list[dict[str, Any]] = []

        while frontier:
            current_urn, depth = frontier.pop(0)
            if depth >= max_depth:
                continue
            for edge in self.get_lineage(current_urn, direction, max_breadth=max_breadth):
                related_urn = edge.get("urn")
                if not related_urn:
                    continue
                enriched = {**edge, "source_urn": current_urn, "depth": depth + 1}
                edges.append(enriched)
                if related_urn not in seen:
                    seen.add(related_urn)
                    frontier.append((related_urn, depth + 1))
        return edges

    def _call_with_retry(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Call a DataHub SDK method with bounded retry/backoff."""
        last_error: Exception | None = None
        for attempt in range(self.settings.retry_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                last_error = exc
                if attempt + 1 >= self.settings.retry_attempts:
                    break
                LOGGER.warning(
                    "DataHub SDK call failed; retrying",
                    extra={
                        "attempt": attempt + 1,
                        "function": getattr(func, "__name__", "unknown"),
                    },
                )
                time.sleep(self.settings.retry_backoff_seconds * (attempt + 1))
        if last_error:
            raise last_error
        raise RuntimeError("DataHub SDK call failed without an exception.")

    def describe_entity(self, urn: str) -> dict[str, Any]:
        """Return a compact metadata description for any supported entity URN.

        Fetches all needed aspects in a single request instead of one
        get_aspect call per aspect, since scan_context calls this once per
        entity in a lineage neighborhood.
        """
        bag = self._call_with_retry(
            self.graph.get_entity_semityped,
            urn,
            aspects=[
                DatasetPropertiesClass.get_aspect_name(),
                MLModelPropertiesClass.get_aspect_name(),
                MLModelDeploymentPropertiesClass.get_aspect_name(),
                OwnershipClass.get_aspect_name(),
                SchemaMetadataClass.get_aspect_name(),
                GlobalTagsClass.get_aspect_name(),
                GlossaryTermsClass.get_aspect_name(),
                UpstreamLineageClass.get_aspect_name(),
            ],
        )
        ownership = bag.get("ownership")
        schema = bag.get("schemaMetadata")
        tags = bag.get("globalTags")
        glossary_terms = bag.get("glossaryTerms")
        return {
            "urn": urn,
            "dataset": self._aspect_to_dict(bag.get("datasetProperties")),
            "model": self._aspect_to_dict(bag.get("mlModelProperties")),
            "deployment": self._aspect_to_dict(bag.get("mlModelDeploymentProperties")),
            "owners": [owner.owner for owner in ownership.owners] if ownership else [],
            "schema": self._schema_fields(schema),
            "tags": [tag.tag for tag in tags.tags] if tags else [],
            "glossary_terms": [term.urn for term in glossary_terms.terms] if glossary_terms else [],
            "upstream_lineage": self._aspect_to_dict(bag.get("upstreamLineage")),
        }

    @staticmethod
    def _aspect_to_dict(aspect: Any | None) -> dict[str, Any]:
        if aspect is None:
            return {}
        if hasattr(aspect, "to_obj"):
            value = aspect.to_obj()
            return value if isinstance(value, dict) else {"value": value}
        if hasattr(aspect, "__dict__"):
            return dict(aspect.__dict__)
        return {"value": aspect}
