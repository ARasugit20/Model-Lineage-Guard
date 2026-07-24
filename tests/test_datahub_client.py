"""Tests for DataHub lineage traversal behavior."""

from typing import Any

from app.datahub_client import DataHubClient, DataHubSettings


class FakeRelated:
    """Minimal DataHub related entity object."""

    def __init__(self, urn: str) -> None:
        self.urn = urn
        self.type = "dataset"
        self.relationship = "DownstreamOf"


class FakeGraph:
    """Mock graph with a cycle and a wide node."""

    def __init__(self) -> None:
        self.calls = 0

    def get_related_entities(self, entity_urn, relationship_types, direction):
        self.calls += 1
        edges = {
            "root": [FakeRelated("a"), FakeRelated("b"), FakeRelated("c")],
            "a": [FakeRelated("root")],
            "b": [FakeRelated("leaf")],
            "c": [],
            "leaf": [],
        }
        return edges.get(entity_urn, [])


class FakeEntityGraph:
    """Mock graph that records semityped entity fetch calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    def get_entity_semityped(self, urn: str, aspects: list[str]) -> dict[str, Any]:
        self.calls.append((urn, aspects))
        return {}


def test_walk_lineage_handles_cycles_and_breadth_limit() -> None:
    client = object.__new__(DataHubClient)
    client.settings = DataHubSettings(gms_host="http://example", retry_attempts=1)
    client.graph = FakeGraph()

    edges = client._walk_lineage("root", "upstream", max_depth=3, max_breadth=2)

    assert [edge["urn"] for edge in edges][:2] == ["a", "b"]
    assert len(edges) == 4
    assert client.graph.calls == 4


def test_describe_entity_fetches_all_aspects_in_one_graph_call() -> None:
    client = object.__new__(DataHubClient)
    client.settings = DataHubSettings(gms_host="http://example", retry_attempts=1)
    client.graph = FakeEntityGraph()

    description = client.describe_entity("urn:li:dataset:(demo,raw,PROD)")

    assert description["urn"] == "urn:li:dataset:(demo,raw,PROD)"
    assert len(client.graph.calls) == 1
    called_urn, aspects = client.graph.calls[0]
    assert called_urn == "urn:li:dataset:(demo,raw,PROD)"
    assert "schemaMetadata" in aspects
    assert "ownership" in aspects


def test_scan_context_describes_each_unique_urn_once() -> None:
    client = object.__new__(DataHubClient)
    client.settings = DataHubSettings(gms_host="http://example", retry_attempts=1)
    describe_calls: list[str] = []

    def walk_lineage(
        urn: str,
        direction: str,
        max_depth: int,
        max_breadth: int,
    ) -> list[dict[str, Any]]:
        del urn, max_depth, max_breadth
        if direction == "upstream":
            return [
                {"urn": "urn:li:dataset:(demo,raw,PROD)", "source_urn": "root", "depth": 1},
                {"urn": "urn:li:dataset:(demo,raw,PROD)", "source_urn": "root", "depth": 1},
            ]
        return [
            {"urn": "urn:li:dataset:(demo,scored,PROD)", "source_urn": "root", "depth": 1},
            {"urn": "urn:li:dataset:(demo,raw,PROD)", "source_urn": "root", "depth": 1},
        ]

    def describe_entity(urn: str) -> dict[str, Any]:
        describe_calls.append(urn)
        return {"urn": urn}

    client._walk_lineage = walk_lineage
    client.get_upstream_lineage = lambda urn: {}
    client.describe_entity = describe_entity

    context = client.scan_context("urn:li:mlModel:(demo,credit_risk,PROD)")

    assert sorted(context["entities"]) == sorted(
        [
            "urn:li:dataset:(demo,raw,PROD)",
            "urn:li:dataset:(demo,scored,PROD)",
            "urn:li:mlModel:(demo,credit_risk,PROD)",
        ]
    )
    assert sorted(describe_calls) == sorted(context["entities"])
