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


def _top_level_bricks(graph: grimp.ImportGraph) -> dict[str, set[str]]:
    """Group polyclean bricks by layer based on their name suffix."""
    layers: dict[str, set[str]] = {
        "contract": set(),
        "flow": set(),
        "adapter": set(),
        "contract_lib": set(),
        "flow_lib": set(),
        "adapter_lib": set(),
        "base": set(),
    }
    seen: set[str] = set()
    for module in graph.modules:
        parts = module.split(".")
        if len(parts) < 2 or parts[0] != "polyclean":  # noqa: PLR2004
            continue
        brick = f"polyclean.{parts[1]}"
        if brick in seen or brick == "polyclean.polyclean":
            continue
        seen.add(brick)
        name = parts[1]
        if name.endswith("_contract_lib"):
            layers["contract_lib"].add(brick)
        elif name.endswith("_flow_lib"):
            layers["flow_lib"].add(brick)
        elif name.endswith("_adapter_lib"):
            layers["adapter_lib"].add(brick)
        elif name.endswith("_contract"):
            layers["contract"].add(brick)
        elif name.endswith("_flow"):
            layers["flow"].add(brick)
        elif name.endswith("_adapter"):
            layers["adapter"].add(brick)
        else:
            layers["base"].add(brick)
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
