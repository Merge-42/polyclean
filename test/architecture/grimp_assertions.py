"""Assertion helpers for grimp-based import graph checks."""

import grimp


def assert_only_imports_from(
    graph: grimp.ImportGraph,
    sources: set[str],
    allowed: set[str],
    all_bricks: set[str],
    rule: str,
) -> None:
    """Fail if any brick in *sources* directly imports a brick outside *allowed*.

    Args:
        graph:      The grimp import graph to query.
        sources:    Bricks whose outgoing imports are being checked.
        allowed:    Bricks that *sources* are permitted to import.
        all_bricks: The complete set of known bricks (used to derive forbidden targets).
        rule:       A short description of the rule shown in the failure message.

    """
    forbidden = all_bricks - allowed - sources

    violations = [
        f"  {src} -> {tgt}"
        for src in sources
        for tgt in forbidden
        if graph.direct_import_exists(importer=src, imported=tgt, as_packages=True)
    ]
    # trunk-ignore(bandit/B101): assert is intentional — this is a test-only helper
    assert not violations, f"Violated rule '{rule}':\n" + "\n".join(violations)
