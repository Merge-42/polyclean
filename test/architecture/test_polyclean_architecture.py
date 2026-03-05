"""Architecture tests for the PolyClean workspace.

Dependency rules (from PolyClean.md):

    Allowed cross-brick imports
    ---------------------------
    flow     -> contract
    adapter  -> contract
    base     -> contract, flow, adapter, *_lib

    Forbidden cross-brick imports
    -----------------------------
    contract -> anything
    flow     -> adapter, flow, base, adapter_lib
    adapter  -> flow, adapter, base, flow_lib
    *_lib    -> may only be imported by their own layer (+ base)
"""

from pathlib import Path

import grimp
import pytest

# ---------------------------------------------------------------------------
# Build graph and classify bricks
# ---------------------------------------------------------------------------


_SUFFIX_TO_LAYER: list[tuple[str, str]] = [
    ("_contract_lib", "contract_lib"),  # checked before _contract
    ("_flow_lib", "flow_lib"),  # checked before _flow
    ("_adapter_lib", "adapter_lib"),  # checked before _adapter
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


def _top_level_bricks(graph: grimp.ImportGraph) -> dict[str, set[str]]:
    """Group polyclean bricks by layer based on their name suffix."""
    layers: dict[str, set[str]] = {layer: set() for _, layer in _SUFFIX_TO_LAYER}
    layers["base"] = set()

    bricks = {
        f"polyclean.{m.split('.')[1]}"
        for m in graph.modules
        if m.startswith("polyclean.") and "." in m
    }
    for brick in bricks:
        layers[_layer_of(brick.split(".")[1])].add(brick)
    return layers


@pytest.fixture(scope="session")
def graph() -> grimp.ImportGraph:
    return grimp.build_graph(
        "polyclean",
        cache_dir=str(Path(".").resolve() / ".grimp_cache"),
    )


@pytest.fixture(scope="session")
def bricks(graph) -> dict[str, set[str]]:
    return _top_level_bricks(graph)


# ---------------------------------------------------------------------------
# Assertion helper
# ---------------------------------------------------------------------------


def assert_no_imports_from(
    graph: grimp.ImportGraph,
    sources: set[str],
    targets: set[str],
    message: str,
) -> None:
    """Fail if any brick in *sources* directly imports any brick in *targets*."""
    violations = [
        f"  {src} -> {tgt}"
        for src in sources
        for tgt in targets
        if src != tgt
        and graph.direct_import_exists(importer=src, imported=tgt, as_packages=True)
    ]
    assert not violations, f"{message}:\n" + "\n".join(violations)


# ---------------------------------------------------------------------------
# Tests — one rule per test, reads like the doc
# ---------------------------------------------------------------------------


def test_contracts_import_nothing(graph, bricks):
    """Contracts are the innermost layer — they may not import any other brick."""
    everything_else = (
        bricks["flow"]
        | bricks["adapter"]
        | bricks["base"]
        | bricks["flow_lib"]
        | bricks["adapter_lib"]
    )
    assert_no_imports_from(
        graph, bricks["contract"], everything_else, "contract -> (anything)"
    )


def test_flows_do_not_import_adapters(graph, bricks):
    """Flows must not know about adapters — ports in contracts mediate instead."""
    assert_no_imports_from(graph, bricks["flow"], bricks["adapter"], "flow -> adapter")


def test_flows_do_not_import_other_flows(graph, bricks):
    """Each flow is an independent use case; flows must not call each other."""
    assert_no_imports_from(graph, bricks["flow"], bricks["flow"], "flow -> flow")


def test_flows_do_not_import_adapter_libs(graph, bricks):
    """Adapter libraries are infrastructure utilities; flows must not use them."""
    assert_no_imports_from(
        graph, bricks["flow"], bricks["adapter_lib"], "flow -> adapter_lib"
    )


def test_adapters_do_not_import_flows(graph, bricks):
    """Adapters implement ports; they must not trigger business logic."""
    assert_no_imports_from(graph, bricks["adapter"], bricks["flow"], "adapter -> flow")


def test_adapters_do_not_import_other_adapters(graph, bricks):
    """Each adapter is an independent integration; put shared code in adapter_lib."""
    assert_no_imports_from(
        graph, bricks["adapter"], bricks["adapter"], "adapter -> adapter"
    )


def test_adapters_do_not_import_flow_libs(graph, bricks):
    """Flow libraries are flow-layer utilities; adapters must not use them."""
    assert_no_imports_from(
        graph, bricks["adapter"], bricks["flow_lib"], "adapter -> flow_lib"
    )


def test_contract_libs_not_used_outside_contracts_and_bases(graph, bricks):
    """contract_libs are scoped to the contract layer (plus base for wiring)."""
    disallowed = (
        bricks["flow"] | bricks["adapter"] | bricks["flow_lib"] | bricks["adapter_lib"]
    )
    assert_no_imports_from(
        graph, disallowed, bricks["contract_lib"], "non-contract/base -> contract_lib"
    )


def test_flow_libs_not_used_outside_flows_and_bases(graph, bricks):
    """flow_libs are scoped to the flow layer (plus base for wiring)."""
    disallowed = (
        bricks["contract"]
        | bricks["adapter"]
        | bricks["contract_lib"]
        | bricks["adapter_lib"]
    )
    assert_no_imports_from(
        graph, disallowed, bricks["flow_lib"], "non-flow/base -> flow_lib"
    )


def test_adapter_libs_not_used_outside_adapters_and_bases(graph, bricks):
    """adapter_libs are scoped to the adapter layer (plus base for wiring)."""
    disallowed = (
        bricks["contract"]
        | bricks["flow"]
        | bricks["contract_lib"]
        | bricks["flow_lib"]
    )
    assert_no_imports_from(
        graph, disallowed, bricks["adapter_lib"], "non-adapter/base -> adapter_lib"
    )
