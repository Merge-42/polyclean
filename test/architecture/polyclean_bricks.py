"""Discovers and classifies PolyClean bricks from the workspace folder layout.

Bases are identified from bases/polyclean/ — the folder is the source of truth.
Components are classified by their name suffix from components/polyclean/.
An unrecognised component suffix raises immediately rather than silently
skipping enforcement.
"""

from pathlib import Path
from types import SimpleNamespace

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


def classify_bricks() -> SimpleNamespace:
    """Return a namespace of sets, one per layer, of fully-qualified brick names.

    Attributes on the returned namespace:
        contract, contract_lib, flow, flow_lib, adapter, adapter_lib, base, all
    """
    layers: dict[str, set[str]] = {layer: set() for _, layer in _SUFFIX_TO_LAYER}
    layers["base"] = set()

    for path in (_WORKSPACE_ROOT / "bases" / "polyclean").iterdir():
        if path.is_dir():
            layers["base"].add(f"polyclean.{path.name}")

    for path in (_WORKSPACE_ROOT / "components" / "polyclean").iterdir():
        if path.is_dir():
            layers[_layer_of_component(path.name)].add(f"polyclean.{path.name}")

    ns = SimpleNamespace(**layers)
    ns.all = set().union(*layers.values())
    return ns
