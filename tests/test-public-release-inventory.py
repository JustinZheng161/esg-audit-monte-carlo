"""Verify the public release inventory and exclude controlled project artifacts."""
from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [path for path in result.stdout.splitlines() if path]


def main() -> None:
    paths = tracked_paths()
    basenames = [PurePosixPath(path).name for path in paths]
    exceptions = {"README.md", "LICENSE", ".gitignore"}
    violations = [name for name in basenames if "_" in name and name not in exceptions]
    assert not violations, f"Tracked basenames contain underscores: {violations}"

    protected_prefixes = (
        "manuscript/",
        "review-round",
        "reproducibility-snapshot/",
        "data/raw/",
        "data/private/",
        "data/restricted/",
    )
    protected = [path for path in paths if path.startswith(protected_prefixes)]
    assert not protected, f"Controlled artifact found in public release: {protected}"
    assert not any("replication-level" in path for path in paths), "Replication-level output is public."
    assert not any(path.endswith((".docx", ".parquet", ".pkl", ".npy")) for path in paths), "Disallowed public binary/data artifact found."

    required = {
        "README.md",
        "config/dgp.yaml",
        "data/public/synthetic-example-null.csv",
        "docs/public-data-and-artifact-catalog.md",
        "docs/publication-figure-specification.md",
        "docs/repository-boundary.md",
        "outputs/publication-figures/figure-source-manifest.json",
        "src/export-publication-figures.py",
        "tests/test-publication-figure-exports.py",
    }
    assert required <= set(paths), f"Missing public inventory entry: {sorted(required - set(paths))}"

    csv_paths = [path for path in paths if path.endswith(".csv")]
    assert len(csv_paths) == 11, f"Unexpected safe public CSV count: {len(csv_paths)}"
    stems = [
        "figure-01-primary-cluster-inference",
        "figure-02-dgp-scale-mapping",
        "figure-03-time-cluster-sensitivity",
        "figure-04-big-four-mechanism-ablation",
        "figure-05-availability-sensitivity",
    ]
    for stem in stems:
        for suffix in (".pdf", ".svg", ".png", ".tiff"):
            path = f"outputs/publication-figures/{stem}{suffix}"
            assert path in paths, f"Missing public publication asset: {path}"

    print("Public release inventory and controlled-boundary checks passed.")


if __name__ == "__main__":
    main()
