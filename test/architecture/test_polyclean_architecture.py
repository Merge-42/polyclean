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
from grimp_assertions import assert_only_imports_from
from polyclean_bricks import classify_bricks


@pytest.fixture(scope="session")
def graph() -> grimp.ImportGraph:
    return grimp.build_graph(
        "polyclean",
        cache_dir=str(Path(".").resolve() / ".grimp_cache"),
    )


@pytest.fixture(scope="session")
def bricks() -> SimpleNamespace:
    return classify_bricks()


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
