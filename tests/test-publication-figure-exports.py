"""Verify public, Nature-style publication figure exports without private inputs."""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / "src" / "export-publication-figures.py"
EXPECTED = {
    "figure-01-primary-cluster-inference": "outputs/final-run-round2-pooled/tables/table-6-independent-seed-crosscheck.csv",
    "figure-02-dgp-scale-mapping": "outputs/round2-pooled/tables/table-11-scale-mapping-pooled.csv",
    "figure-03-time-cluster-sensitivity": "outputs/round2-pooled/tables/table-10-time-structure-sensitivity-pooled.csv",
    "figure-04-big-four-mechanism-ablation": "outputs/round2-big4-pooled/tables/table-9-big4-mechanism-ablation-pooled.csv",
    "figure-05-availability-sensitivity": "outputs/round2-pooled/tables/table-12-selective-availability-pooled.csv",
}
FORMATS = {"pdf", "svg", "png", "tiff"}
CANVAS_PIXELS = {
    "figure-01-primary-cluster-inference": (4320, 2520),
    "figure-02-dgp-scale-mapping": (4320, 2520),
    "figure-03-time-cluster-sensitivity": (4320, 2160),
    "figure-04-big-four-mechanism-ablation": (4320, 2520),
    "figure-05-availability-sensitivity": (4320, 2520),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_dpi(path: Path) -> tuple[float, float]:
    """Read the PNG pHYs chunk using only the Python standard library."""
    raw = path.read_bytes()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", f"Invalid PNG signature: {path.name}"
    position = 8
    while position < len(raw):
        size = struct.unpack(">I", raw[position:position + 4])[0]
        chunk = raw[position + 4:position + 8]
        data = raw[position + 8:position + 8 + size]
        position += 12 + size
        if chunk == b"pHYs":
            x_ppm, y_ppm, unit = struct.unpack(">IIB", data)
            assert unit == 1, f"PNG has non-metric pHYs units: {path.name}"
            return (x_ppm * 0.0254, y_ppm * 0.0254)
    raise AssertionError(f"PNG is missing pHYs metadata: {path.name}")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="publication-figure-check-") as temp:
        output = Path(temp) / "figures"
        subprocess.run([sys.executable, str(EXPORTER), "--output", str(output)], check=True)
        manifest = json.loads((output / "figure-source-manifest.json").read_text(encoding="utf-8"))

        assert manifest["schema_version"] == 1
        records = {record["stem"]: record for record in manifest["figures"]}
        assert set(records) == set(EXPECTED)

        for stem, source in EXPECTED.items():
            record = records[stem]
            source_path = ROOT / source
            assert source_path.is_file(), f"Public aggregate table missing: {source}"
            assert record["generator"] == "src/export-publication-figures.py"
            assert record["source_table"] == source
            assert record["source_table_sha256"] == sha256(source_path)
            assert set(record["assets"]) == FORMATS

            for suffix, expected_hash in record["assets"].items():
                asset = output / f"{stem}.{suffix}"
                assert asset.is_file() and asset.stat().st_size > 0, f"Missing {suffix}: {stem}"
                assert sha256(asset) == expected_hash, f"Hash mismatch: {asset.name}"

            svg = (output / f"{stem}.svg").read_text(encoding="utf-8")
            assert "<text" in svg and "font-family" in svg, f"SVG text is not editable: {stem}"
            assert "#d9d9d9" not in svg.lower(), f"Nature-style export retained a background grid: {stem}"
            assert (output / f"{stem}.pdf").read_bytes().startswith(b"%PDF"), f"Invalid PDF: {stem}"
            assert (output / f"{stem}.tiff").read_bytes()[:4] in {b"II*\x00", b"MM\x00*"}, f"Invalid TIFF: {stem}"
            png = output / f"{stem}.png"
            dpi = png_dpi(png)
            assert all(abs(value - 600.0) < 1.0 for value in dpi), f"PNG is not 600 dpi: {stem}, {dpi}"
            raw = png.read_bytes()
            dimensions = struct.unpack(">II", raw[16:24])
            assert dimensions == CANVAS_PIXELS[stem], f"Unexpected Nature canvas: {stem}, {dimensions}"

    print("Nature-style publication figure export tests passed.")


if __name__ == "__main__":
    main()
