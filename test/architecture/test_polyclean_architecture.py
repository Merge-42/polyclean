"""Architecture tests for the PolyClean workspace using Grimp.

Whitelists (cross-brick polyclean imports only):
  contracts   -> contracts, contract_libs
  flows       -> contracts, flow_libs
  adapters    -> contracts, adapter_libs
  bases       -> contracts, flows, adapters, contract_libs, flow_libs, adapter_libs
  *_lib       -> may only be imported by their own layer (+ bases)
"""

import re
from pathlib import Path
from types import SimpleNamespace

import grimp
import pytest

# ---------------------------------------------------------------------------
# Discovery helpers
# ---------------------------------------------------------------------------

_PATTERNS: dict[str, re.Pattern[str]] = {
    "contract": re.compile(r"_contract$"),
    "flow": re.compile(r"_flow$"),
    "adapter": re.compile(r"_adapter$|_adapter(?!_lib)\w*$"),
    "contract_lib": re.compile(r"_contract_lib$"),
    "flow_lib": re.compile(r"_flow_lib$"),
    "adapter_lib": re.compile(r"_adapter_lib$"),
}


def _brick(module: str) -> str:
    """Return the top-level brick (first two dotted parts: polyclean.foo)."""
    parts = module.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else module  # noqa: PLR2004


def _classify(brick: str) -> str | None:
    """Return the category of a brick, or None if it is a base."""
    for category, pat in _PATTERNS.items():
        if pat.search(brick):
            return category
    return None  # treated as base


def _expand(modules: set[str], bricks: set[str]) -> set[str]:
    """All modules that belong to the given bricks."""
    return {m for m in modules if _brick(m) in bricks}


# ---------------------------------------------------------------------------
# Fixture: build graph + classify bricks once per session
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def arch() -> SimpleNamespace:
    """Return a namespace object with the graph and pre-classified module sets."""
    graph: grimp.ImportGraph = grimp.build_graph(
        "polyclean",
        cache_dir=str(Path(".").resolve() / ".grimp_cache"),
    )
    all_modules: set[str] = graph.modules

    bricks: dict[str, set[str]] = {cat: set() for cat in _PATTERNS}
    bricks["base"] = set()

    for m in all_modules:
        b: str = _brick(m)
        cat: str | None = _classify(b)
        bricks[cat if cat else "base"].add(b)

    sets: dict[str, set[str]] = {
        cat: _expand(all_modules, bricks[cat]) for cat in bricks
    }

    ns = SimpleNamespace(
        graph=graph,
        all_modules=all_modules,
        **sets,
    )
    # whitelists per layer (cross-brick polyclean.* allowed imports)
    ns.whitelists = {
        "contract": sets["contract"] | sets["contract_lib"],
        "flow": sets["contract"] | sets["flow_lib"],
        "adapter": sets["contract"] | sets["adapter_lib"],
        "base": sets["contract"]
        | sets["flow"]
        | sets["adapter"]
        | sets["contract_lib"]
        | sets["flow_lib"]
        | sets["adapter_lib"],
    }
    return ns


# ---------------------------------------------------------------------------
# Generic rule: every cross-brick polyclean import must be in the whitelist
# ---------------------------------------------------------------------------


def _check_whitelist(arch, layer: str) -> list[str]:
    """Return violation strings for every out-of-whitelist cross-brick import."""
    layer_modules: set[str] = getattr(arch, layer)
    whitelist: set[str] = arch.whitelists[layer]
    violations: list[str] = []

    for mod in layer_modules:
        for imp in arch.graph.find_modules_directly_imported_by(mod):
            # skip intra-brick and non-polyclean (stdlib / third-party)
            if _brick(imp) == _brick(mod) or imp not in arch.all_modules:
                continue
            if imp not in whitelist:
                violations.append(f"{mod} -> {imp}")

    return violations


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_contracts(arch):
    """Contracts may only import contracts and contract_libs."""
    v = _check_whitelist(arch, "contract")
    assert not v, "Contract whitelist violations:\n" + "\n".join(v)


def test_flows(arch):
    """Flows may only import contracts and flow_libs."""
    v = _check_whitelist(arch, "flow")
    assert not v, "Flow whitelist violations:\n" + "\n".join(v)


def test_adapters(arch):
    """Adapters may only import contracts and adapter_libs."""
    v = _check_whitelist(arch, "adapter")
    assert not v, "Adapter whitelist violations:\n" + "\n".join(v)


def test_bases(arch):
    """Bases may import contracts, flows, adapters, and any libs."""
    v = _check_whitelist(arch, "base")
    assert not v, "Base whitelist violations:\n" + "\n".join(v)


def test_contract_libs_not_leaked(arch):
    """contract_libs may only be imported by contracts and bases."""
    allowed = arch.contract | arch.base
    v = [
        f"{imp} -> {lib}"
        for lib in arch.contract_lib
        for imp in arch.graph.find_modules_that_directly_import(lib)
        if imp not in allowed and _brick(imp) != _brick(lib)
    ]
    assert not v, "contract_lib leakage:\n" + "\n".join(v)


def test_flow_libs_not_leaked(arch):
    """flow_libs may only be imported by flows and bases."""
    allowed = arch.flow | arch.base
    v = [
        f"{imp} -> {lib}"
        for lib in arch.flow_lib
        for imp in arch.graph.find_modules_that_directly_import(lib)
        if imp not in allowed and _brick(imp) != _brick(lib)
    ]
    assert not v, "flow_lib leakage:\n" + "\n".join(v)


def test_adapter_libs_not_leaked(arch):
    """adapter_libs may only be imported by adapters and bases."""
    allowed = arch.adapter | arch.base
    v = [
        f"{imp} -> {lib}"
        for lib in arch.adapter_lib
        for imp in arch.graph.find_modules_that_directly_import(lib)
        if imp not in allowed and _brick(imp) != _brick(lib)
    ]
    assert not v, "adapter_lib leakage:\n" + "\n".join(v)
