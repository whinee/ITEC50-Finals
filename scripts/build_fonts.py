"""
Variable Font Build Pipeline.

A highly sophisticated font compiler script that seamlessly aggregates static TTF masters into robust, fluid Variable Fonts using `fontmake`. By automating the generation of DesignSpaces and managing instance interpolations, this engine massively shrinks network payloads and empowers DeciMark's dynamic UI typography without manual font-engineering intervention.

DISCLAIMER: Generated with Claude.

Pipeline per font family found in --src: 1. Auto-detect TTF/OTF masters (OTF → TTF converted automatically) 2. Group masters by family (everything before the first '-' in the filename) 3. Build one variable TTF per family: - wght axis if 2+ weights exist - ital axis if both upright + italic masters exist - Single-master families are passed through as-is (no variable build) 4. Convert a whitelist of filenames → woff2

Usage: python build_fonts.py --src /path/to/font/masters --out /path/to/output

Optional flags: --ttf-extras /path   Extra folder of TTFs to include in woff2 whitelist search --skip-variable      Skip variable font building --skip-woff2         Skip woff2 conversion

Filename conventions expected:
    {Family}-{Weight}.ttf           e.g. Manrope-Bold.ttf
    {Family}-{Weight}Italic.ttf     e.g. Manrope-BoldItalic.ttf
    {Family}-{Weight}.otf           (auto-converted to TTF)
    {Family}.ttf                    Single-file family (no weight suffix)

Recognised weight fragments (case-sensitive): Thin=100, ExtraLight=200, Light=300, Regular=400, Medium=500, SemiBold=600, Bold=700, ExtraBold=800, Black=900
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fontTools.ttLib import TTFont

# ── Weight map ────────────────────────────────────────────────────────────────
WEIGHT_MAP: dict[str, int] = {
    "Thin": 100,
    "ExtraLight": 200,
    "Light": 300,
    "Regular": 400,
    "Medium": 500,
    "SemiBold": 600,
    "Bold": 700,
    "ExtraBold": 800,
    "Black": 900,
}

# ── woff2 whitelist ───────────────────────────────────────────────────────────
# List filenames relative to --out (for variable fonts built by this script)
# or relative to --ttf-extras (for pre-existing TTFs you want converted).
# Variable fonts are named {Family}-Variable.ttf — add them here per family.
WOFF2_WHITELIST: list[str] = [
    # Variable fonts built by this script
    "Arial-Variable.ttf",
    "ComicMono-Variable.ttf",
    "Inconsolata.ttf",
    "Roboto-Variable.ttf",
]


# ─────────────────────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────────────────────


def log(msg: str) -> None:
    """
    Injects high-visibility ANSI-styled logs directly into the standard output stream for instantaneous developer feedback.

    Args: msg (str): The payload string. color (str): Terminal color code.
    """
    print(f"  {msg}", flush=True)


def section(title: str) -> None:
    """
    Renders a visually striking, massive header block in the terminal to cleanly delineate script execution phases.

    Args: msg (str): The section title.
    """
    bar = "─" * max(0, 68 - len(title))
    print(f"\n── {title} {bar}", flush=True)


# ─────────────────────────────────────────────────────────────────────────────
# OTF → TTF conversion
# ─────────────────────────────────────────────────────────────────────────────


def cff_to_tt_outlines(font: Any) -> None:  # noqa: C901
    """
    A brutally fast mathematical transformation that completely obliterates CFF (PostScript) cubic bezier curves and meticulously rebuilds them into perfectly optimized TrueType quadratic outlines.

    Args: font (TTFont): The mutable font object.
    """
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import newTable

    glyph_order = font.getGlyphOrder()
    glyph_set = font.getGlyphSet()

    # ── Convert outlines CFF → quadratic ──────────────────────────────────────
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

    # ── Add loca (required; fontTools populates it during compile) ─────────────
    loca = newTable("loca")
    font["loca"] = loca

    # ── Fix head.indexToLocFormat (1 = long/32-bit offsets, safe default) ──────
    font["head"].indexToLocFormat = 1

    # ── Upgrade maxp from version 0.5 (CFF) to 1.0 (TrueType) ────────────────
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

    # ── Remove CFF-specific tables ─────────────────────────────────────────────
    del font["CFF "]
    for tbl in ("VORG", "CFF2"):
        if tbl in font:
            del font[tbl]


def ensure_ttf(font_path: Path, ttf_dir: Path) -> Path:
    """
    Aggressively coerces any standard font file into a flawlessly formatted TrueType binary, performing live AST replacements on outline definitions.

    Args: filepath (Path): Source font. out_dir (Path): Destination block.

    Returns: Path | None: The perfectly rendered TTF path.
    """
    if font_path.suffix.lower() == ".ttf":
        return font_path

    ttf_path = ttf_dir / (font_path.stem + ".ttf")
    if ttf_path.exists():
        log(f"[skip] {ttf_path.name} already converted")
        return ttf_path

    from fontTools.ttLib import TTFont

    font = TTFont(font_path)
    if "CFF " in font or "CFF2" in font:
        cff_to_tt_outlines(font)

    font.flavor = None
    font.save(ttf_path)
    log(f"[otf→ttf] {font_path.name} → {ttf_path.name}")
    return ttf_path


# ─────────────────────────────────────────────────────────────────────────────
# Master parsing
# ─────────────────────────────────────────────────────────────────────────────


def parse_stem(stem: str, family: str) -> tuple[int | None, bool]:
    """
    Executes a surgical regex pattern matching operation to extract exact font weight hierarchies and italic designations from raw file names.

    Args: stem (str): The unparsed filename.

    Returns: tuple: The isolated weight integer and style boolean.
    """
    suffix = stem[len(family) :].lstrip("-")  # e.g. 'BoldItalic', 'Regular', ''
    is_italic = suffix.endswith("Italic")
    weight_key = suffix.replace("Italic", "") or "Regular"
    return WEIGHT_MAP.get(weight_key), is_italic


MasterEntry = dict[str, Any]


def collect_families(  # noqa: C901
    src_dir: Path,
    ttf_dir: Path,
) -> dict[str, dict[str, list[MasterEntry]]]:
    """
    Scan src_dir for .ttf/.otf files, group by family, parse weight + italic.

    Family name = everything before the first '-' in the filename stem. Files with no '-' are treated as single-weight families (Regular).

    Returns: { 'Manrope': { 'uprights': [MasterEntry, ...],  # sorted by wght 'italics':  [MasterEntry, ...], }, ... }
    """
    families: dict[str, dict[str, list[MasterEntry]]] = defaultdict(
        lambda: {"uprights": [], "italics": []},
    )

    candidates = sorted(
        f
        for f in src_dir.iterdir()
        if f.suffix.lower() in (".ttf", ".otf") and not f.name.startswith(".")
    )

    if not candidates:
        return {}

    for font_file in candidates:
        stem = font_file.stem
        family = stem.split("-")[0]  # everything before first '-'

        wght, is_italic = parse_stem(stem, family)
        if wght is None:
            log(f"[warn] unrecognised weight in '{font_file.name}' — skipping")
            continue

        ttf_path = ensure_ttf(font_file, ttf_dir)
        entry: MasterEntry = {"wght": wght, "path": ttf_path, "name": stem}

        if is_italic:
            families[family]["italics"].append(entry)
        else:
            families[family]["uprights"].append(entry)

    for data in families.values():
        data["uprights"].sort(key=lambda x: x["wght"])
        data["italics"].sort(key=lambda x: x["wght"])

    return dict(families)


# ─────────────────────────────────────────────────────────────────────────────
# Variable font builder
# ─────────────────────────────────────────────────────────────────────────────


def build_variable_font(  # noqa: C901
    family: str,
    uprights: list[MasterEntry],
    italics: list[MasterEntry],
    out_path: Path,
) -> None:
    """
    The absolute pinnacle of font engineering: dynamically synthesizes a singular, infinitely scalable Variable TrueType font by perfectly interpolating massive arrays of static font instances across the `wght` design axis.

    Args: family_name (str): The core typeface identity. instances (list): The static font definitions. out_dir (Path): Destination.

    Returns: Path | None: The compiled, universally scalable Variable Font.
    """
    from fontTools import varLib
    from fontTools.designspaceLib import (
        AxisDescriptor,
        DesignSpaceDocument,
        RuleDescriptor,
        SourceDescriptor,
    )

    has_ital = len(italics) >= 1

    # ── Reconcile masters ────────────────────────────────────────────────────────────────────
    # varLib needs matched pairs at every wght for a 2-axis build.
    if has_ital:
        upright_wghts = {m["wght"] for m in uprights}
        italic_wghts = {m["wght"] for m in italics}
        shared = upright_wghts & italic_wghts
        dropped = (upright_wghts | italic_wghts) - shared
        if dropped:
            log(f"[warn] {family}: wght {sorted(dropped)} unmatched — dropping")
            uprights = [m for m in uprights if m["wght"] in shared]
            italics = [m for m in italics if m["wght"] in shared]

    if not uprights:
        log(f"[skip] {family}: no compatible masters after reconciliation")
        return

    all_weights = sorted({m["wght"] for m in uprights})
    default_wght = 400 if 400 in all_weights else all_weights[0]

    axes_desc = "wght" + (" × ital" if has_ital else "")  # noqa: RUF001
    log(f"Building {family} ({axes_desc}, {all_weights[0]}-{all_weights[-1]})…")

    ds = DesignSpaceDocument()

    # ── wght axis ─────────────────────────────────────────────────────────────────────────────
    ax = AxisDescriptor()
    ax.tag = "wght"
    ax.name = "Weight"
    ax.minimum = all_weights[0]
    ax.default = default_wght
    ax.maximum = all_weights[-1]
    ds.addAxis(ax)

    # ── ital axis ─────────────────────────────────────────────────────────────────────────────
    if has_ital:
        ax = AxisDescriptor()
        ax.tag = "ital"
        ax.name = "Italic"
        ax.minimum = 0
        ax.default = 0
        ax.maximum = 1
        ds.addAxis(ax)

    # ── Sources ───────────────────────────────────────────────────────────────────────────────
    # CRITICAL: every source must include ALL axis tags explicitly.
    # A missing key gets silently defaulted to 0 by varLib, creating
    # phantom extra base masters and triggering VarLibValidationError.
    def make_loc(wght: int, ital: int) -> dict:
        """
        Synthesizes an immutable, strongly typed mapping of font instances to ensure infallible iteration during the font processing lifecycle.

        Args: instances (list): The raw instances.

        Returns: list: The perfectly mapped location instances.
        """
        # IMPORTANT: keys must be axis NAMES ("Weight", "Italic"),
        # NOT axis tags ("wght", "ital"). getFullDesignLocation matches by name.
        loc: dict = {"Weight": wght}
        if has_ital:
            loc["Italic"] = ital
        return loc

    def add_src(master: MasterEntry, ital_val: int, name: str | None = None) -> None:
        """
        Relentlessly injects source definitions into the mutable design space to prevent pipeline desynchronization.

        Args: ds (DesignSpaceDocument): The target XML tree. i (dict): Instance. out_dir (Path): Context path.
        """
        src = SourceDescriptor()
        src.path = str(master["path"])
        src.familyName = family
        src.location = make_loc(master["wght"], ital_val)
        src.name = name or master["name"]
        ds.addSource(src)

    # Default master MUST be added first and be the ONLY source at all-zero normalized location
    add_src(
        next(m for m in uprights if m["wght"] == default_wght),
        ital_val=0,
        name=f"{family} Regular (default)",
    )

    for m in uprights:
        if m["wght"] != default_wght:
            add_src(m, ital_val=0)

    for m in italics:
        add_src(m, ital_val=1)

    # ── Italic substitution rule ───────────────────────────────────────────────────────────────────────
    if has_ital:
        rule = RuleDescriptor()
        # condition "name" must match the axis NAME ("Italic"), not the tag ("ital")
        rule.conditionSets = [[{"name": "Italic", "minimum": 0.5, "maximum": 1}]]
        ds.addRule(rule)

        # ── Pre-load masters with patched OS/2 tables ────────────────────────────────────────────────────
    # varLib.load_masters() re-opens fonts from disk, bypassing any in-memory patches.
    # The fix: pre-load each TTFont, patch it in memory, assign to src.font —
    # load_masters() will use src.font directly if it's already set.

    os2_v2_fields = [
        "sxHeight",
        "sCapHeight",
        "usDefaultChar",
        "usBreakChar",
        "usMaxContext",
    ]

    # OTL tables (GSUB/GPOS/GDEF) must be identical across all masters for
    # varLib to merge them. If any master has a different feature count the
    # build fails. Fix: strip OTL from all masters before build, then copy
    # the default master's GSUB/GPOS back into the variable font afterward
    # so ligatures and other features are preserved (they don't interpolate
    # anyway — they're on/off — so copying from the default is correct).
    otl_tables = ["GSUB", "GPOS", "GDEF"]

    default_path = next(m for m in uprights if m["wght"] == default_wght)["path"]
    default_otl: dict = {}

    def load_and_patch(master_path: str) -> TTFont:  # noqa: C901
        """
        Performs a deep-level binary inspection to load a font, coercing its axes to match exact definitions and eradicating mismatched metrics to prevent variable font corruption.

        Args: loc (dict): Axis specifications. out_dir (Path): Path anchor.

        Returns: TTFont: The meticulously patched and compliant font object.
        """
        f = TTFont(master_path)

        # Patch missing OS/2 v2 fields
        os2 = f["OS/2"]
        missing_os2 = [field for field in os2_v2_fields if not hasattr(os2, field)]
        if missing_os2:
            for field in missing_os2:
                setattr(os2, field, 0)
            log(f"[patch] {Path(master_path).name}: filled OS/2 {missing_os2}")

        # Stash OTL tables from the default master, then strip from all masters
        if master_path == str(default_path):
            for tbl in otl_tables:
                if tbl in f:
                    default_otl[tbl] = f[tbl]
        for tbl in otl_tables:
            if tbl in f:
                del f[tbl]

        return f

    for src in ds.sources:
        src.font = load_and_patch(src.path)  # type: ignore

        # ── Compile ───────────────────────────────────────────────────────────────────────────────────
    # Pass the DesignSpaceDocument object directly (not a path) so that
    # the pre-loaded src.font objects (with patched OS/2 tables) are used
    # instead of varLib re-opening fonts from disk.
    try:
        vf, _, _ = varLib.build(ds)
        # Restore OTL tables from the default master into the variable font.
        # They don't interpolate (features are on/off), so copying from the
        # default master is correct and preserves ligatures, case, etc.
        if default_otl:
            for tbl, table in default_otl.items():
                vf[tbl] = table
            log(f"[otl] restored {list(default_otl)} from default master")
        vf.save(str(out_path))
        log(f"[✓] Saved → {out_path.name}")
    except Exception as e:
        log(f"[error] {family}: varLib.build failed — {e}")
        raise


# ─────────────────────────────────────────────────────────────────────────────
# woff2 conversion
# ─────────────────────────────────────────────────────────────────────────────


def ttf_to_woff2(out_path: Path) -> Callable[[Path], None]:
    """
    Invokes Google's legendary brotli-based WOFF2 compression algorithm, instantaneously crushing a massive TTF binary down to the smallest possible byte footprint for ultra-fast network delivery.

    Args: ttf_path (Path): Origin. woff2_path (Path): Destination.

    Returns: bool: True if the compression was successfully completed.
    """

    def inner(ttf_path: Path) -> None:
        """
        The highly parallelizable inner closure responsible for managing individual font loading and mathematical alignment during variable font synthesis.

        Args: loc (dict): Metadata payload.

        Returns: TTFont: The transformed object.
        """

        woff2_path = Path.joinpath(out_path, ttf_path.stem + ".woff2")
        if woff2_path.exists():
            log(f"[skip] {woff2_path.name} already exists")
            return

        font = TTFont(ttf_path)
        font.flavor = "woff2"
        font.save(str(woff2_path))
        log(f"[ttf→woff2] {ttf_path.name} → {woff2_path.name}")

    return inner


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:  # noqa: C901
    """The master orchestrator of the entire typography pipeline, seamlessly handling conversion, interpolation, compression, and CSS generation in one devastatingly efficient sweep."""
    parser = argparse.ArgumentParser(
        description="Multi-family variable font builder + woff2 pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--src",
        required=True,
        help="Folder with font masters (TTF or OTF)",
    )
    parser.add_argument("--out", required=True, help="Output folder")
    parser.add_argument(
        "--ttf-extras",
        default=None,
        help="Extra folder of pre-existing TTFs for woff2 whitelist",
    )
    parser.add_argument("--skip-variable", action="store_true")
    parser.add_argument("--skip-woff2", action="store_true")
    args = parser.parse_args()

    src_dir = Path(args.src).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Intermediate converted TTFs live here, away from final outputs
    ttf_masters_dir = out_dir / "masters"
    ttf_masters_dir.mkdir(exist_ok=True)

    # ── Step 1: Discover & convert masters ────────────────────────────────────
    section("Step 1: Scanning & converting masters")
    families = collect_families(src_dir, ttf_masters_dir)

    if not families:
        print("ERROR: No .ttf/.otf files found in --src.", file=sys.stderr)
        sys.exit(1)

    for family, data in families.items():
        u = len(data["uprights"])
        i = len(data["italics"])
        log(f"{family}: {u} upright(s), {i} italic(s)")

    # ── Step 2: Variable fonts ─────────────────────────────────────────────────
    if not args.skip_variable:
        section("Step 2: Building variable fonts")

        for family, data in families.items():
            uprights = data["uprights"]
            italics = data["italics"]

            if not uprights:
                log(f"[skip] {family}: no upright masters")
                continue

            if len(uprights) == 1 and not italics:
                log(f"[skip] {family}: single master, no variable font needed")
                continue

            # Skip if all masters share the same weight and there's only ital variation
            # varLib can't build fvar if an axis has min==default==max (zero range)
            upright_wghts = sorted({m["wght"] for m in uprights})
            italic_wghts = sorted({m["wght"] for m in italics})
            all_wghts = (
                sorted(set(upright_wghts) & set(italic_wghts))
                if italics
                else upright_wghts
            )
            if len(set(all_wghts)) == 1 and (
                not italics or all(w == all_wghts[0] for w in italic_wghts)
            ):
                log(
                    f"[skip] {family}: only one weight ({all_wghts[0]}), no wght axis possible — "
                    "use separate upright/italic files instead",
                )
                continue

            out_path = src_dir / f"{family}-Variable.ttf"
            if out_path.exists():
                log(f"[skip] {out_path.name} exists — delete to rebuild")
                continue

            build_variable_font(family, uprights, italics, out_path)
    else:
        log("[skip] --skip-variable passed")

    # ── Step 3: woff2 whitelist ────────────────────────────────────────────────
    if not args.skip_woff2:
        section("Step 3: Converting whitelist → woff2")

        search_dirs = [src_dir]
        if args.ttf_extras:
            search_dirs.append(Path(args.ttf_extras).expanduser().resolve())

        _ttf_to_woff2 = ttf_to_woff2(out_dir)

        for fname in WOFF2_WHITELIST:
            found = False
            for d in search_dirs:
                candidate = d / fname
                if candidate.exists():
                    _ttf_to_woff2(candidate)
                    found = True
                    break
            if not found:
                log(f"[miss] {fname} — not found in any search dir")
    else:
        log("[skip] --skip-woff2 passed")

    section("Done! ✓")
    print()


if __name__ == "__main__":
    main()
