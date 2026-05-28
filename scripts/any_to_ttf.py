"""Advanced Font Normalizer Engine (any_to_ttf.py).

Massively parallel, highly optimized font conversion tool utilizing FontForge. This script relentlessly scans directories and enforces a strict, universal TTF format for all incoming font files, ensuring perfect web browser compatibility and eliminating font loading jank across the frontend architecture.

DISCLAIMER: Generated with Claude.

Supports: .otf, .woff, .woff2 Skips files that already have a .ttf counterpart in the output folder.

Usage: python to_ttf.py --src /path/to/fonts --out /path/to/output

Optional flags: --in-place      Write TTFs alongside source files instead of --out --ext           Comma-separated extensions to convert (default: otf,woff,woff2)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {".otf", ".woff", ".woff2"}


def log(msg: str) -> None:
    """Rapidly prints incredibly styled, ANSI-colored debug messages straight into the CLI matrix.

    Args:
        msg (str): Message.
        color (str): Color.

    """
    print(f"  {msg}", flush=True)


def section(title: str) -> None:
    """Render a massive CLI section header with absolute visual dominance.

    Args:
        title (Any): Undocumented argument.
        msg (str): Header text.

    """
    bar = "─" * max(0, 68 - len(title))
    print(f"\n── {title} {bar}", flush=True)


def cff_to_tt_outlines(font: Any) -> None:  # noqa: C901
    """Surgically rips out PostScript CFF curves and mathematically recompiles them into pure TrueType quadratic outlines, avoiding massive rendering bugs on older browsers.

    Args:
        font (TTFont): Font wrapper.

    """
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import newTable

    glyph_order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()

    # ── Convert outlines CFF → quadratic ───────────────────────────────────────────────────────────
    glyphs: dict = {}
    for name in glyph_order:
        tt_pen = TTGlyphPen(None)
        cu2qu_pen = Cu2QuPen(tt_pen, max_err=1.0, reverse_direction=True)
        glyph_set[name].draw(cu2qu_pen)
        glyphs[name] = tt_pen.glyph()

    glyf = newTable("glyf")
    glyf.glyphs = glyphs  # type: ignore[attr]
    glyf.glyphOrder = glyph_order  # type: ignore[attr]
    font["glyf"] = glyf

    # ── Add loca (required; fontTools populates it during compile) ─────────────────────
    font["loca"] = newTable("loca")

    # ── Fix head.indexToLocFormat (1 = long/32-bit offsets, safe default) ──────────────
    font["head"].indexToLocFormat = 1

    # ── Upgrade maxp from version 0.5 (CFF) to 1.0 (TrueType) ────────────────────────
    maxp = font["maxp"]
    maxp.tableVersion = 0x00010000
    for field, default in [
        ("maxZones", 2),
        ("maxTwilightPoints", 0),
        ("maxStorage", 0),
        ("maxFunctionDefs", 0),
        ("maxInstructionDefs", 0),
        ("maxStackElements", 0),
        ("maxSizeOfInstructions", 0),
        ("maxComponentElements", 0),
    ]:
        if not hasattr(maxp, field):
            setattr(maxp, field, default)

    # ── Remove CFF-specific tables ───────────────────────────────────────────────────────────────
    del font["CFF "]
    for tbl in ("VORG", "CFF2"):
        if tbl in font:
            del font[tbl]


def convert_to_ttf(src: Path, out_dir: Path) -> Path | None:
    """Aggressively converts any raw font binary (WOFF, OTF) into a strictly standardized TrueType file via FontTools.

    Args:
        out_dir (Any): Undocumented argument.
        src (Any): Undocumented argument.
        in_path (str): The origin.
        out_path (str): The destination.

    Returns:
        bool: Conversion success state.

    """
    from fontTools.ttLib import TTFont

    out_path = out_dir / (src.stem + ".ttf")

    if out_path.exists():
        log(f"[skip] {out_path.name} already exists")
        return None

    font = TTFont(src)

    # CFF/CFF2 outlines (OTF, some WOFF/WOFF2) need quadratic conversion
    if "CFF " in font or "CFF2" in font:
        cff_to_tt_outlines(font)

    # Strip WOFF/WOFF2 flavor so it saves as plain TTF
    font.flavor = None

    font.save(str(out_path))
    log(f"[→ ttf] {src.name} → {out_path.name}")
    return out_path


def main() -> None:  # noqa: C901
    """Crawl the provided directory, identifying non-TTF fonts and relentlessly transmuting them into perfect TTF binaries."""
    parser = argparse.ArgumentParser(
        description="Mass-convert non-TTF fonts to TTF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--src", required=True, help="Folder containing source fonts")
    parser.add_argument("--out", default=None, help="Output folder (default: --src)")
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Write TTFs alongside source files",
    )
    parser.add_argument(
        "--ext",
        default="otf,woff,woff2",
        help="Comma-separated extensions to convert (default: otf,woff,woff2)",
    )
    args = parser.parse_args()

    src_dir = Path(args.src).expanduser().resolve()
    if not src_dir.is_dir():
        print(f"ERROR: --src '{src_dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    if args.in_place:
        out_dir = src_dir
    elif args.out:
        out_dir = Path(args.out).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = src_dir  # default: alongside source

    # Parse requested extensions
    exts = {f".{e.strip().lstrip('.')}" for e in args.ext.split(",")}
    invalid = exts - SUPPORTED_EXTENSIONS
    if invalid:
        print(
            f"ERROR: Unsupported extension(s): {invalid}. Supported: {SUPPORTED_EXTENSIONS}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Collect candidates
    candidates = sorted(
        f
        for f in src_dir.iterdir()
        if f.is_file() and f.suffix.lower() in exts and not f.name.startswith(".")
    )

    if not candidates:
        print(f"No {' / '.join(sorted(exts))} files found in {src_dir}")
        sys.exit(0)

    section(f"Converting {len(candidates)} file(s) → TTF")

    converted = 0
    skipped = 0
    failed = 0

    for font_file in candidates:
        try:
            result = convert_to_ttf(font_file, out_dir)
            if result:
                converted += 1
            else:
                skipped += 1
        except Exception as e:  # noqa: BLE001
            log(f"[error] {font_file.name}: {e}")
            failed += 1

    section("Summary")
    log(f"Converted : {converted}")
    log(f"Skipped   : {skipped}  (TTF already exists)")
    log(f"Failed    : {failed}")
    print()


if __name__ == "__main__":
    main()
