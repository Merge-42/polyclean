"""Architecture tests for the PolyClean workspace.

Each test asserts that all cross-brick imports from a layer land only in
the layers it is allowed to depend on (from PolyClean.md):

    Layer         May import from
    ------------  ----------------------------------
    contract      contract, contract_lib
    contract_lib  contract, contract_lib
    flow          contract, contract_lib, flow_lib
    flow_lib      contract, contract_lib, flow_lib
    adapter       contract, contract_lib, adapter_lib
    adapter_lib   contract, contract_lib, adapter_lib
    base          (everything — no restriction)
"""

from pathlib import Path
from types import SimpleNamespace

import grimp
import pytest

# ---------------------------------------------------------------------------
# Brick discovery
# ---------------------------------------------------------------------------

# Longer suffixes listed first so '_contract_lib' matches before '_contract', etc.
_SUFFIX_TO_LAYER: list[tuple[str, str]] = [
    ("_contract_lib", "contract_lib"),
    ("_flow_lib", "flow_lib"),
    ("_adapter_lib", "adapter_lib"),
    ("_contract", "contract"),
    ("_flow", "flow"),
    ("_adapter", "adapter"),
]


def _layer_of(brick_name: str) -> str:
    """Return the layer for a brick given its short name (e.g. 'create_post_flow')."""
    return next(
        (layer for suffix, layer in _SUFFIX_TO_LAYER if brick_name.endswith(suffix)),
        "base",
    )


def _classify_bricks(graph: grimp.ImportGraph) -> SimpleNamespace:
    """Return a namespace of sets, one per layer, containing fully-qualified brick names."""
    layers: dict[str, set[str]] = {layer: set() for _, layer in _SUFFIX_TO_LAYER}
    layers["base"] = set()

    bricks = {
        f"polyclean.{m.split('.')[1]}"
        for m in graph.modules
        if m.startswith("polyclean.") and "." in m
    }
    for brick in bricks:
        layers[_layer_of(brick.split(".")[1])].add(brick)

    return SimpleNamespace(**layers)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def graph() -> grimp.ImportGraph:
    return grimp.build_graph(
        "polyclean",
        cache_dir=str(Path(".").resolve() / ".grimp_cache"),
    )


@pytest.fixture(scope="session")
def bricks(graph) -> SimpleNamespace:
    return _classify_bricks(graph)


# ---------------------------------------------------------------------------
# Assertion helper
# ---------------------------------------------------------------------------


def assert_only_imports_from(
    graph: grimp.ImportGraph,
    sources: set[str],
    allowed: set[str],
    rule: str,
) -> None:
    """Fail if any brick in *sources* imports a polyclean brick outside *allowed*."""
    all_bricks = {
        f"polyclean.{m.split('.')[1]}"
        for m in graph.modules
        if m.startswith("polyclean.") and "." in m
    }
    forbidden = all_bricks - allowed - sources

    violations = [
        f"  {src} -> {tgt}"
        for src in sources
        for tgt in forbidden
        if graph.direct_import_exists(importer=src, imported=tgt, as_packages=True)
    ]
    assert not violations, f"Violated rule '{rule}':\n" + "\n".join(violations)


# ---------------------------------------------------------------------------
# Tests — one per layer, asserts the full allowed-import whitelist
# ---------------------------------------------------------------------------


def test_contracts_may_only_import_contract_layer(graph, bricks):
    """Contracts are the innermost layer; they depend on nothing outside contracts."""
    assert_only_imports_from(
        graph,
        sources=bricks.contract,
        allowed=bricks.contract | bricks.contract_lib,
        rule="contract -> contract | contract_lib",
    )


def test_contract_libs_may_only_import_contract_layer(graph, bricks):
    """contract_libs support the contract layer and share the same boundary."""
    assert_only_imports_from(
        graph,
        sources=bricks.contract_lib,
        allowed=bricks.contract | bricks.contract_lib,
        rule="contract_lib -> contract | contract_lib",
    )


def test_flows_may_only_import_contract_and_flow_layer(graph, bricks):
    """Flows orchestrate contracts; they must not reach into adapters or other flows."""
    assert_only_imports_from(
        graph,
        sources=bricks.flow,
        allowed=bricks.contract | bricks.contract_lib | bricks.flow_lib,
        rule="flow -> contract | contract_lib | flow_lib",
    )


def test_flow_libs_may_only_import_contract_and_flow_layer(graph, bricks):
    """flow_libs support the flow layer and share the same boundary."""
    assert_only_imports_from(
        graph,
        sources=bricks.flow_lib,
        allowed=bricks.contract | bricks.contract_lib | bricks.flow_lib,
        rule="flow_lib -> contract | contract_lib | flow_lib",
    )


def test_adapters_may_only_import_contract_and_adapter_layer(graph, bricks):
    """Adapters implement ports; they must not reach into flows or other adapters."""
    assert_only_imports_from(
        graph,
        sources=bricks.adapter,
        allowed=bricks.contract | bricks.contract_lib | bricks.adapter_lib,
        rule="adapter -> contract | contract_lib | adapter_lib",
    )


def test_adapter_libs_may_only_import_contract_and_adapter_layer(graph, bricks):
    """adapter_libs support the adapter layer and share the same boundary."""
    assert_only_imports_from(
        graph,
        sources=bricks.adapter_lib,
        allowed=bricks.contract | bricks.contract_lib | bricks.adapter_lib,
        rule="adapter_lib -> contract | contract_lib | adapter_lib",
    )


def test_bases_may_import_anything(graph, bricks):
    """Bases are the composition root — no import restrictions apply.

    This test is intentionally a no-op today. It exists to document the rule
    and to act as a placeholder if restrictions are added in the future.
    """
    all_layers = (
        bricks.contract
        | bricks.contract_lib
        | bricks.flow
        | bricks.flow_lib
        | bricks.adapter
        | bricks.adapter_lib
        | bricks.base
    )
    assert_only_imports_from(
        graph,
        sources=bricks.base,
        allowed=all_layers,
        rule="base -> (everything)",
    )
