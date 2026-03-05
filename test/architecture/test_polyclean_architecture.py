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

_WORKSPACE_ROOT = Path(__file__).parent.parent.parent

# Longer suffixes listed first so '_contract_lib' matches before '_contract', etc.
_SUFFIX_TO_LAYER: list[tuple[str, str]] = [
    ("_contract_lib", "contract_lib"),
    ("_flow_lib", "flow_lib"),
    ("_adapter_lib", "adapter_lib"),
    ("_contract", "contract"),
    ("_flow", "flow"),
    ("_adapter", "adapter"),
]


def _layer_of_component(name: str) -> str:
    """Return the layer for a component brick, or raise if the suffix is unrecognised.

    Raises rather than defaulting to 'base' so that a misplaced or misspelled
    component is caught immediately rather than silently skipping enforcement.
    """
    layer = next(
        (layer for suffix, layer in _SUFFIX_TO_LAYER if name.endswith(suffix)),
        None,
    )
    if layer is None:
        raise ValueError(
            f"Component '{name}' has an unrecognised suffix. "
            f"Expected one of: {[s for s, _ in _SUFFIX_TO_LAYER]}. "
            f"Base bricks must live under bases/polyclean/, not components/polyclean/."
        )
    return layer


def _classify_bricks() -> SimpleNamespace:
    """Return a namespace of sets, one per layer, containing fully-qualified brick names.

    Base bricks are discovered from bases/polyclean/ (folder layout is the source of truth).
    Component bricks are classified by suffix from components/polyclean/.
    An unrecognised component suffix raises immediately.
    """
    layers: dict[str, set[str]] = {layer: set() for _, layer in _SUFFIX_TO_LAYER}
    layers["base"] = set()

    base_dirs = (_WORKSPACE_ROOT / "bases" / "polyclean").iterdir()
    component_dirs = (_WORKSPACE_ROOT / "components" / "polyclean").iterdir()

    for path in base_dirs:
        if path.is_dir():
            layers["base"].add(f"polyclean.{path.name}")

    for path in component_dirs:
        if path.is_dir():
            layers[_layer_of_component(path.name)].add(f"polyclean.{path.name}")

    ns = SimpleNamespace(**layers)
    ns.all = set().union(*layers.values())
    return ns


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
def bricks() -> SimpleNamespace:
    return _classify_bricks()


# ---------------------------------------------------------------------------
# Assertion helper
# ---------------------------------------------------------------------------


def assert_only_imports_from(
    graph: grimp.ImportGraph,
    sources: set[str],
    allowed: set[str],
    all_bricks: set[str],
    rule: str,
) -> None:
    """Fail if any brick in *sources* imports a polyclean brick outside *allowed*."""
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
        all_bricks=bricks.all,
        rule="contract -> contract | contract_lib",
    )


def test_contract_libs_may_only_import_contract_layer(graph, bricks):
    """contract_libs support the contract layer and share the same boundary."""
    assert_only_imports_from(
        graph,
        sources=bricks.contract_lib,
        allowed=bricks.contract | bricks.contract_lib,
        all_bricks=bricks.all,
        rule="contract_lib -> contract | contract_lib",
    )


def test_flows_may_only_import_contract_and_flow_layer(graph, bricks):
    """Flows orchestrate contracts; they must not reach into adapters or other flows."""
    assert_only_imports_from(
        graph,
        sources=bricks.flow,
        allowed=bricks.contract | bricks.contract_lib | bricks.flow_lib,
        all_bricks=bricks.all,
        rule="flow -> contract | contract_lib | flow_lib",
    )


def test_flow_libs_may_only_import_contract_and_flow_layer(graph, bricks):
    """flow_libs support the flow layer and share the same boundary."""
    assert_only_imports_from(
        graph,
        sources=bricks.flow_lib,
        allowed=bricks.contract | bricks.contract_lib | bricks.flow_lib,
        all_bricks=bricks.all,
        rule="flow_lib -> contract | contract_lib | flow_lib",
    )


def test_adapters_may_only_import_contract_and_adapter_layer(graph, bricks):
    """Adapters implement ports; they must not reach into flows or other adapters."""
    assert_only_imports_from(
        graph,
        sources=bricks.adapter,
        allowed=bricks.contract | bricks.contract_lib | bricks.adapter_lib,
        all_bricks=bricks.all,
        rule="adapter -> contract | contract_lib | adapter_lib",
    )


def test_adapter_libs_may_only_import_contract_and_adapter_layer(graph, bricks):
    """adapter_libs support the adapter layer and share the same boundary."""
    assert_only_imports_from(
        graph,
        sources=bricks.adapter_lib,
        allowed=bricks.contract | bricks.contract_lib | bricks.adapter_lib,
        all_bricks=bricks.all,
        rule="adapter_lib -> contract | contract_lib | adapter_lib",
    )


def test_bases_may_import_anything(graph, bricks):
    """Bases are the composition root — no import restrictions apply.

    This test is intentionally a no-op today. It exists to document the rule
    and to act as a placeholder if restrictions are added in the future.
    """
    assert_only_imports_from(
        graph,
        sources=bricks.base,
        allowed=bricks.all,
        all_bricks=bricks.all,
        rule="base -> (everything)",
    )
