r"""
Python Documentation Summarizer.

Extracts module-level documentation from all project Python files using pdoc3,
converts the resulting Markdown-Extra output to LaTeX fragments, and writes them
into ``paper/python-summaries/`` as individual ``.tex`` files. Generates two
index files:

- ``paper/python-summaries/index.tex``      — one ``\section`` per module with
  its docstring rendered as LaTeX.
- ``paper/python-summaries/index-code.tex`` — one ``\section`` per module with
  the raw source inlined via ``\inputmintedstyledtwocolumns``.

Module discovery covers:
- ``main.py`` in the project root
- Everything under ``src/`` and ``scripts/``
- Excludes ``src/migrations/``, ``__init__.py`` files that are empty, and
  ``.history/`` artefacts.
"""

import ast
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pypandoc

# ── project root ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# ── output dirs ───────────────────────────────────────────────────────────────

TEX_OUTPUT_DIR = PROJECT_ROOT / "paper" / "python-summaries"
TEX_MAIN_PAPER_DIR = PROJECT_ROOT / "paper"

# ── file discovery ────────────────────────────────────────────────────────────

EXCLUDE_PATTERNS: list[str] = [
    "migrations",
    ".history",
    ".venv",
    "__pycache__",
    "tests",
]


def _is_excluded(path: Path) -> bool:
    """Return True if *path* matches any exclusion pattern."""
    parts = path.parts
    return any(ex in parts or any(ex in p for p in parts) for ex in EXCLUDE_PATTERNS)


def resolve_python_files() -> list[Path]:  # noqa: C901
    """
    Discover all project Python files in deterministic sorted order.

    Searches ``main.py``, ``scripts/``, and ``src/``, applying the exclusion
    list and skipping empty ``__init__.py`` files that carry no module docstring.

    Returns:
        list[Path]: Sorted list of absolute ``Path`` objects.

    """
    candidates: list[Path] = []

    for pattern in ["main.py", "scripts/**/*.py", "src/**/*.py"]:
        candidates.extend(PROJECT_ROOT.glob(pattern))

    result: list[Path] = []
    for p in sorted(set(candidates)):
        if _is_excluded(p):
            continue
        if p.name == "__init__.py":
            # Skip __init__.py files that carry no module docstring
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"))
                doc = ast.get_docstring(tree)
                if not doc:
                    continue
            except SyntaxError:
                continue
        result.append(p)

    return result


# ── module name resolution ────────────────────────────────────────────────────


def path_to_module(path: Path) -> str:
    """
    Convert an absolute file path to a dotted Python module name.

    ``/project/src/api/bookmarks.py`` → ``src.api.bookmarks``

    Args:
        path (Path): Absolute path to the ``.py`` file.

    Returns:
        str: Dotted module name importable from the project root.

    """
    rel = path.relative_to(PROJECT_ROOT)
    parts = list(rel.with_suffix("").parts)
    return ".".join(parts)


# ── pdoc3 invocation ──────────────────────────────────────────────────────────


def run_pdoc3(module: str) -> str:
    """
    Invoke ``pdoc3 --pdf`` for the given module and return its stdout.

    Args:
        module (str): Dotted module name.

    Returns:
        str: Raw Markdown-Extra output from pdoc3.

    Raises:
        RuntimeError: If pdoc3 exits with a non-zero status.

    """
    result = subprocess.run(  # noqa: S603
        ["uv", "run", "pdoc3", "--pdf", module],  # noqa: S607
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode not in (0, 1):
        # pdoc3 exits 1 even on success sometimes; treat >1 as error
        raise RuntimeError(
            f"pdoc3 failed for {module} (exit {result.returncode}):\n{result.stderr}",
        )
    return result.stdout


# ── markdown → LaTeX conversion ───────────────────────────────────────────────


def md_to_tex(md: str, base_section_depth: int = 2) -> str:
    """
    Convert a Markdown fragment to a LaTeX fragment suitable for direct inclusion.

    Uses `pypandoc` to convert the markdown to LaTeX.

    Args:
        md (str): The Markdown input string.
        base_section_depth (int): LaTeX depth offset (2 = subsection for ##).

    Returns:
        str: LaTeX fragment (no preamble).

    """
    # Adjust headings in markdown before passing to pandoc so that # becomes \subsection, etc.
    # A base_section_depth of 2 means # -> ##
    lines = md.splitlines()
    adjusted_lines = []
    for line in lines:
        if line.startswith("#"):
            adjusted_lines.append("#" * (base_section_depth - 1) + line)
        else:
            adjusted_lines.append(line)

    adjusted_md = "\n".join(adjusted_lines)

    return pypandoc.convert_text(adjusted_md, "latex", format="markdown")


# ── extract module-level section from pdoc3 output ────────────────────────────


def extract_module_section(pdoc_output: str) -> str:
    """
    Strip the YAML front-matter from pdoc3 output and extract only the module doc.

    This extracts everything before the first ``## `` subsection such as
    ``## Functions`` or ``## Classes``.

    Args:
        pdoc_output (str): Full stdout from ``pdoc3 --pdf``.

    Returns:
        str: Isolated module-level Markdown block.

    """
    # Strip YAML front matter (between --- ... ---)
    text = re.sub(r"^---.*?\.\.\.\s*", "", pdoc_output, flags=re.DOTALL)

    # Find the "# Module `name`" heading
    module_heading_match = re.search(r"^# Module `[^`]+`.*?$", text, re.MULTILINE)
    if not module_heading_match:
        return text.replace(
            "Generated by pdoc 0.11.6 (https://pdoc3.github.io).",
            "",
        ).strip()

    body = text[module_heading_match.end() :]

    # Cut off at the first ## subsection (Functions, Classes, etc.)
    sub_match = re.search(r"^## ", body, re.MULTILINE)
    if sub_match:
        body = body[: sub_match.start()]

    return body.strip()


# ── tex escaping (minimal, for section titles) ────────────────────────────────


def _tex_escape_title(text: str) -> str:
    """
    Escape characters that would break a LaTeX section title.

    Handles only the characters that legitimately appear in Python module paths.

    Args:
        text (str): The raw title string.

    Returns:
        str: The escaped title.

    """
    return (
        text.replace("_", r"\_")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("#", r"\#")
        .replace("$", r"\$")
    )


# ── per-file tex generation ───────────────────────────────────────────────────


def generate_tex_for_module(
    path: Path,
    module: str,
    pdoc_output: str,
) -> str:
    r"""
    Produce a complete LaTeX fragment for a single Python module.

    Includes the module path, generation timestamp, the module-level docstring
    rendered as LaTeX prose, and a horizontal rule footer.

    Args:
        path (Path): Absolute path to the source file.
        module (str): Dotted module name.
        pdoc_output (str): Raw pdoc3 Markdown output.

    Returns:
        str: LaTeX fragment (no preamble, no ``\begin{document}``).

    """
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    rel_path = path.relative_to(PROJECT_ROOT)
    title = _tex_escape_title(str(rel_path))
    module_escaped = _tex_escape_title(module)

    md_body = extract_module_section(pdoc_output)
    tex_body = md_to_tex(md_body)

    lines: list[str] = [
        f"% Python module: {module}",
        f"% Generated: {date_str}",
        "",
        r"\section{\texttt{" + title + r"}}",
        r"\textit{Module: \texttt{" + module_escaped + r"}} \\",
        r"\textit{Generated: " + date_str + r"} \\",
        "",
        tex_body,
        "",
    ]
    return "\n".join(lines)


# ── index generators ──────────────────────────────────────────────────────────


def generate_tex_index(tex_files: list[Path]) -> str:
    r"""
    Generate ``index.tex`` manifest of ``\input{}`` calls for module docstrings.

    Args:
        tex_files (list[Path]): Absolute paths to the generated ``.tex`` files.

    Returns:
        str: Contents of ``index.tex``.

    """
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "% Python Documentation Index",
        f"% Generated: {date_str}",
        "",
    ]
    for tex_path in tex_files:
        rel = tex_path.relative_to(TEX_MAIN_PAPER_DIR)
        lines.append(f"\\input{{./{rel}}}")
    lines.append("")
    return "\n".join(lines)


def generate_tex_code_index(py_files: list[Path]) -> str:
    r"""
    Generate ``index-code.tex`` manifest that inlines each Python source file.

    It inlines each file via ``\inputmintedstyled``.

    Args:
        py_files (list[Path]): Absolute paths to the Python source files.

    Returns:
        str: Contents of ``index-code.tex``.

    """
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "% Python Source Code Index",
        f"% Generated: {date_str}",
        "",
    ]
    for py_path in py_files:
        rel_from_project = py_path.relative_to(PROJECT_ROOT)
        title = _tex_escape_title(str(rel_from_project))
        # Path relative to paper/ for \inputmintedstyled (walk_up for files outside paper/)
        rel_from_paper = py_path.absolute().relative_to(
            TEX_MAIN_PAPER_DIR,
            walk_up=True,
        )
        lines.append(r"\section{\texttt{" + title + r"}}")
        lines.append(
            r"\inputmintedstyled{python}{" + str(rel_from_paper) + "}",
        )
        lines.append(r"\newpage")
    lines.append("")
    return "\n".join(lines)


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:  # noqa: C901
    """
    Orchestrate the full Python documentation pipeline.

    Discovers all Python source files, runs pdoc3 on each, converts the
    module-level Markdown to LaTeX, writes individual fragment files, and
    emits ``index.tex`` and ``index-code.tex`` to ``paper/python-summaries/``.
    """
    TEX_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("── Discovering Python files...")
    py_files = resolve_python_files()
    if not py_files:
        print("  ✗ No Python files found.")
        sys.exit(1)
    print(f"  ✓ {len(py_files)} file(s):")
    for f in py_files:
        print(f"    {f.relative_to(PROJECT_ROOT)}")

    processed_tex: list[Path] = []
    processed_py: list[Path] = []

    for py_path in py_files:
        module = path_to_module(py_path)
        rel = py_path.relative_to(PROJECT_ROOT)
        print(f"\n── Processing: {rel} ({module})")

        try:
            pdoc_output = run_pdoc3(module)
        except RuntimeError as e:
            print(f"  ✗ pdoc3 error: {e}")
            continue

        tex_content = generate_tex_for_module(py_path, module, pdoc_output)
        # Strip box drawing characters to prevent xelatex font crash
        tex_content = re.sub(r"[\u2500-\u257F]", "-", tex_content)

        # Mirror the source tree inside python-summaries/
        rel_no_ext = rel.with_suffix(".tex")
        tex_out = TEX_OUTPUT_DIR / rel_no_ext
        tex_out.parent.mkdir(parents=True, exist_ok=True)
        tex_out.write_text(tex_content, encoding="utf-8")
        print(f"  ✓ TEX → {tex_out.relative_to(PROJECT_ROOT)}")

        processed_tex.append(tex_out)
        processed_py.append(py_path)

    if not processed_tex:
        print("\n  ✗ Nothing processed successfully.")
        sys.exit(1)

    print("\n── Generating index files...")

    index_path = TEX_OUTPUT_DIR / "index.tex"
    index_path.write_text(generate_tex_index(processed_tex), encoding="utf-8")
    print(f"  ✓ TEX index      → {index_path.relative_to(PROJECT_ROOT)}")

    code_index_path = TEX_OUTPUT_DIR / "index-code.tex"
    code_index_path.write_text(
        generate_tex_code_index(processed_py),
        encoding="utf-8",
    )
    print(f"  ✓ TEX code index → {code_index_path.relative_to(PROJECT_ROOT)}")

    print(f"\n── Done! Processed {len(processed_tex)} file(s).")


if __name__ == "__main__":
    main()
