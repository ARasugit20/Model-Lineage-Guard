"""Tests for DataHub lineage traversal behavior."""

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


def test_walk_lineage_handles_cycles_and_breadth_limit() -> None:
    client = object.__new__(DataHubClient)
    client.settings = DataHubSettings(gms_host="http://example", retry_attempts=1)
    client.graph = FakeGraph()

    edges = client._walk_lineage("root", "upstream", max_depth=3, max_breadth=2)

    assert [edge["urn"] for edge in edges][:2] == ["a", "b"]
    assert len(edges) == 4
    assert client.graph.calls == 4
