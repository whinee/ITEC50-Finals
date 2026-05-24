r"""
summarize_css.py: Lint and summarize CSS files' structures.

DISCLAIMER: Generated with Claude, duly modified.

For each CSS file resolved by the include/exclude config:
  1. Parses /* SECTION - SUBSECTION: START/END */ comment blocks into a tree
  2. Handles inline (non-START/END) comments as leaf nodes owning the next
       selector
  3. Lints for mismatched START/END pairs
  4. Generates a Markdown summary  → MD_OUTPUT_DIR/<stem>.md
  5. Generates a LaTeX summary    → TEX_OUTPUT_DIR/<stem>.tex  (no preamble)

Then generates index files:
  - MD_OUTPUT_DIR/index.md   (links to all per-file .md docs)
  - TEX_OUTPUT_DIR/index.tex (\input{} for all per-file .tex docs)

── Include/exclude resolution order ─────────────────────────────────────────---
  1. Collect all candidates from INCLUDE (folders, files, globs).
  2. Remove anything matched by EXCLUDE (folders, files, globs).
  3. Deduplicate, sort. The result is the final file list.

  Folders are searched recursively for *.css files.
  Globs are evaluated relative to the current working directory.
  Exclusion by folder removes any file whose path is inside that folder.
"""

import fnmatch
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# ── config ────────────────────────────────────────────────────────────────────

ROOT_FOLDER = Path("src/static/stylesheets")

INCLUDE = {
    # Folders to search recursively for *.css files
    "folders": [
        ".",
    ],
    # Specific files to always include
    "files": [],
    # Glob patterns (relative to cwd)
    "globs": [],
}

EXCLUDE = {
    # Any .css file inside these folders will be excluded
    "folders": [
        "./downloaded",  # vendor CSS — don't document these
    ],
    # Specific files to always exclude
    "files": [],
    # Glob patterns to exclude (relative to cwd)
    "globs": [
        "**/*.back.css",
    ],
}

MD_OUTPUT_DIR = "docs/css-summaries"
TEX_OUTPUT_DIR = "paper/css-summaries"
TEX_MAIN_PAPER_DIR = "paper/"

TEX_OUTPUT_DIR_REL_MAIN_PAPER = (
    f"./{Path(TEX_OUTPUT_DIR).relative_to(TEX_MAIN_PAPER_DIR)}"
)

# ── file resolution ───────────────────────────────────────────────────────────


def resolve_files() -> list[str]:  # noqa: C901
    """Resolves the final list of CSS files to process based on INCLUDE/EXCLUDE. Returns a sorted, deduplicated list of relative path strings."""
    candidates: set[Path] = set()

    # ── inclusions ────────────────────────────────────────────────────────────
    for folder in INCLUDE.get("folders", []):
        p = ROOT_FOLDER / Path(folder)
        if p.is_dir():
            candidates.update(p.rglob("*.css"))
        else:
            print(f"  ⚠ Include folder not found, skipping: {folder}")

    for file in INCLUDE.get("files", []):
        p = ROOT_FOLDER / Path(file)
        if p.is_file():
            candidates.add(p)
        else:
            print(f"  ⚠ Include file not found, skipping: {file}")

    for glob in INCLUDE.get("globs", []):
        matched = list(ROOT_FOLDER.glob(glob))
        if not matched:
            print(f"  ⚠ Include glob matched nothing: {glob}")
        candidates.update(f for f in matched if f.suffix == ".css" and f.is_file())

    # ── exclusions ────────────────────────────────────────────────────────────
    excluded: set[Path] = set()

    exclude_folder_paths = [
        (ROOT_FOLDER / f).resolve() for f in EXCLUDE.get("folders", [])
    ]

    for candidate in candidates:
        resolved = candidate.resolve()

        # excluded folder: any file whose resolved path is inside the folder
        for ef in exclude_folder_paths:
            try:
                resolved.relative_to(ef)
                excluded.add(candidate)
                break
            except ValueError:
                pass

    for file in EXCLUDE.get("files", []):
        p = ROOT_FOLDER / Path(file)
        excluded.update(c for c in candidates if c.resolve() == p.resolve())

    for glob in EXCLUDE.get("globs", []):
        for candidate in candidates:
            if fnmatch.fnmatch(str(candidate), str(ROOT_FOLDER / glob)):
                excluded.add(candidate)

    final = sorted(candidates - excluded, key=lambda p: str(p))
    return [str(p) for p in final]


# ── data model ────────────────────────────────────────────────────────────────


@dataclass
class CSSNode:
    """A node in the section tree."""

    name: str  # e.g. "COLORS" or "BACKGROUND - #1"
    full_path: str  # e.g. "VARIABLES > COLORS > BACKGROUND"
    depth: int  # nesting depth (0 = root sections)
    is_inline: bool = False  # True = inline comment (no START/END)
    children: list["CSSNode"] = field(default_factory=list)
    line_start: int | None = None
    line_end: int | None = None


@dataclass
class LintError:
    line: int
    message: str


# ── parsing ───────────────────────────────────────────────────────────────────

COMMENT_RE = re.compile(r"/\*\s*(.*?)\s*\*/")
START_END_RE = re.compile(r"^(.*?):\s*(START|END)$", re.IGNORECASE)
SELECTOR_RE = re.compile(r"^\s*([^{]+)\{")


def split_path(label: str) -> list[str]:
    """'VARIABLES - COLORS - BG' → ['VARIABLES', 'COLORS', 'BG']."""
    return [p.strip() for p in label.split(" - ")]


def next_non_blank_selector(lines: list[str], after: int) -> str | None:
    """
    Scans forward from `after` for the next line that looks like a CSS selector.

    Returns None if the next meaningful line looks like a property declaration
    (e.g. `--bg-1: hsl(...)` or `background-color: var(...)`) rather than a
    selector (which must contain `{`).
    """
    for i in range(after + 1, min(after + 6, len(lines))):
        line = lines[i].strip()
        if not line or line.startswith(("/*", "//")):
            continue
        m = SELECTOR_RE.match(lines[i])
        if m:
            return m.group(1).strip()
        # if the line has a colon but no `{`, it's a property declaration — skip
        return None
    return None


def parse_css(path: str) -> tuple[list[CSSNode], list[LintError]]:  # noqa: C901
    """Parses a CSS file into a flat-then-nested list of CSSNodes and returns lint errors for mismatched START/END pairs."""
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()

    lint_errors: list[LintError] = []

    # ── pass 1: collect all comments with their line numbers ─────────────────
    @dataclass
    class RawComment:
        line: int
        text: str

    raw_comments: list[RawComment] = []
    for i, line in enumerate(lines, start=1):
        m = COMMENT_RE.search(line)
        if m:
            raw_comments.append(RawComment(line=i, text=m.group(1).strip()))

    # ── pass 2: identify start/end pairs vs inline comments ──────────────────
    @dataclass
    class Event:
        line: int
        label: str  # full label without ": START/END"
        parts: list[str]  # split path
        kind: str  # "start" | "end" | "inline"

    events: list[Event] = []
    for rc in raw_comments:
        m = START_END_RE.match(rc.text)
        if m:
            label = m.group(1).strip()
            kind = m.group(2).upper()
            events.append(
                Event(
                    line=rc.line,
                    label=label,
                    parts=split_path(label),
                    kind=kind.lower(),
                ),
            )
        else:
            events.append(
                Event(
                    line=rc.line,
                    label=rc.text,
                    parts=split_path(rc.text),
                    kind="inline",
                ),
            )

    # ── pass 3: lint START/END matching ──────────────────────────────────────
    # track open starts: label → list of line numbers (stack per label)
    open_starts: dict[str, list[int]] = {}
    for ev in events:
        if ev.kind == "start":
            open_starts.setdefault(ev.label, []).append(ev.line)
        elif ev.kind == "end":
            if ev.label not in open_starts or not open_starts[ev.label]:
                lint_errors.append(
                    LintError(
                        line=ev.line,
                        message=f"END without matching START: '{ev.label}'",
                    ),
                )
            else:
                open_starts[ev.label].pop()

    for label, lines_open in open_starts.items():
        for ln in lines_open:
            lint_errors.append(
                LintError(
                    line=ln,
                    message=f"START without matching END: '{label}'",
                ),
            )

    lint_errors.sort(key=lambda e: e.line)

    # ── pass 4: build section tree from start/end + inline events ────────────
    # We use a stack to track the current open section path.
    # Each item on the stack is a CSSNode.

    roots: list[CSSNode] = []
    stack: list[CSSNode] = []  # currently open block nodes

    def current_path_str(extra_parts: list[str]) -> str:
        base = [s.name for s in stack]
        return " > ".join(base + extra_parts)

    def find_or_create_child(
        parent_list: list[CSSNode],
        name: str,
        full_path: str,
        depth: int,
    ) -> CSSNode:
        for c in parent_list:
            if c.name == name and not c.is_inline:
                return c
        node = CSSNode(name=name, full_path=full_path, depth=depth)
        parent_list.append(node)
        return node

    def insert_node(
        parts: list[str],
    ) -> CSSNode | None:
        """Inserts a node into the tree at the right depth, guided by the parts list and the currently open stack. Returns the deepest node created/found."""
        # The parts represent the FULL path from root.
        # We reconcile with the current stack to find the right insertion point.
        target_list = roots
        node = None
        for depth, part in enumerate(parts):
            full = " > ".join(parts[: depth + 1])
            node = find_or_create_child(target_list, part, full, depth)
            target_list = node.children
        return node

    for ev in events:
        node = insert_node(ev.parts)
        if ev.kind == "start":
            if node:
                node.line_start = ev.line
                # push the deepest new node onto the stack
                # but only if it isn't already there
                if not stack or stack[-1] is not node:
                    stack.append(node)
        elif ev.kind == "end":
            if node:
                node.line_end = ev.line
                # pop stack back to parent of this node
                if stack and stack[-1] is node:
                    stack.pop()

        elif ev.kind == "inline":
            # Inline comment: belongs under whatever is currently open on the stack
            parent_list = stack[-1].children if stack else roots
            depth = len(stack)
            full_path = current_path_str(ev.parts)
            inline_node = CSSNode(
                name=ev.label,
                full_path=full_path,
                depth=depth,
                is_inline=True,
                line_start=ev.line,
            )
            parent_list.append(inline_node)

    return roots, lint_errors


# ── ascii tree ────────────────────────────────────────────────────────────────


def _ascii_tree_lines(nodes: list, prefix: str = "") -> list[str]:
    """Recursively renders a list of CSSNodes as ASCII tree lines. Uses classic tree(1) box-drawing characters."""
    out: list[str] = []
    # filter out inline nodes with no selector (bare annotation comments)
    visible = [n for n in nodes if not n.is_inline]
    for i, node in enumerate(visible):
        is_last = i == len(visible) - 1
        connector = "└── " if is_last else "├── "
        child_pfx = prefix + ("    " if is_last else "│   ")

        # build the label
        label = node.name
        if not node.is_inline and node.line_start:
            loc = f"line {node.line_start}"
            if node.line_end:
                loc += f"-{node.line_end}"
            label += f"  ({loc})"

        out.append(f"{prefix}{connector}{label}")
        if node.children:
            out.extend(_ascii_tree_lines(node.children, child_pfx))
    return out


def render_ascii_tree(roots: list) -> str:  # noqa: C901
    """Returns a full ASCII tree string for a list of root CSSNodes."""
    if not roots:
        return "(no sections)"
    lines: list[str] = ["."]
    visible_roots = [n for n in roots if not n.is_inline]
    for i, root in enumerate(visible_roots):
        is_last = i == len(visible_roots) - 1
        connector = "└── " if is_last else "├── "
        child_pfx = "    " if is_last else "│   "

        label = root.name
        if not root.is_inline and root.line_start:
            loc = f"line {root.line_start}"
            if root.line_end:
                loc += f"-{root.line_end}"
            label += f"  ({loc})"

        lines.append(connector + label)
        if root.children:
            lines.extend(_ascii_tree_lines(root.children, child_pfx))
    return "\n".join(lines)


# ── markdown generation ───────────────────────────────────────────────────────


def generate_md(
    css_path: str,
    roots: list[CSSNode],
    lint_errors: list[LintError],
) -> str:
    lines: list[str] = [
        f"# CSS Summary: `{Path(css_path).relative_to(ROOT_FOLDER)!s}`",
        "",
        f"> Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
        f"> Source: `{css_path}`",
        "",
    ]

    # lint section
    lines.append("## Lint Results")
    if lint_errors:
        lines.append(f"> ⚠️ {len(lint_errors)} issue(s) found\n")
        for err in lint_errors:
            lines.append(f"- **Line {err.line}**: {err.message}")
    else:
        lines.append("> ✅ No lint issues found.")
    lines.append("")

    # section tree — ascii overview
    lines.append("## Section Tree")
    lines.append("")
    lines.append("```")
    lines.append(render_ascii_tree(roots))
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


# ── latex generation ──────────────────────────────────────────────────────────


def tex_escape(text: str) -> str:
    """Escapes special LaTeX characters."""
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
        (">", r"\textgreater{}"),
        ("<", r"\textless{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def generate_tex(
    css_path: str,
    roots: list[CSSNode],
    lint_errors: list[LintError],
) -> str:
    filename_escaped = tex_escape(str(Path(css_path).relative_to(ROOT_FOLDER)))
    path_escaped = tex_escape(css_path)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines: list[str] = [
        f"% CSS Summary: {filename_escaped}",
        f"% Generated: {date_str}",
        f"% Source: {path_escaped}",
        r"",
        r"\section{" + f"{filename_escaped}" + r"}",
        r"\textit{Source: \texttt{" + path_escaped + r"}} \\",
        r"\textit{Generated: " + tex_escape(date_str) + r"} \\",
        r"",
    ]

    # lint
    lines.append(r"\subsection{Lint Results}")
    if lint_errors:
        lines.append(r"\begin{itemize}")
        for err in lint_errors:
            lines.append(
                r"  \item \textbf{Line "
                + str(err.line)
                + r":} "
                + tex_escape(err.message),
            )
        lines.append(r"\end{itemize}")
    else:
        lines.append(r"\textit{No lint issues found.} \\")
    lines.append(r"")

    lines.append(r"\subsection{Section Tree}")
    lines.append(r"\begingroup")
    lines.append(r"\linespread{0.9}\selectfont")
    lines.append(r"\begin{verbnobox}[\FiraCode]")
    lines.append(render_ascii_tree(roots))
    lines.append(r"\end{verbnobox}")
    lines.append(r"\endgroup")

    return "\n".join(lines)


# ── index generation ──────────────────────────────────────────────────────────


def generate_md_index(css_files: list[str], md_dir: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# CSS Documentation Index",
        "",
        f"> Generated on {date_str}",
        "",
        "## Files",
        "",
    ]
    for css_path in css_files:
        rel = Path(css_path).relative_to(ROOT_FOLDER)
        md_name = rel.with_suffix(".md")
        lines.append(f"- [{rel}](./{md_name})")
    lines.append("")
    return "\n".join(lines)


def generate_tex_index(css_files: list[str], tex_dir: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "% CSS Documentation Index",
        f"% Generated: {date_str}",
        r"",
    ]
    for css_path in css_files:
        rel = Path(css_path).relative_to(ROOT_FOLDER)
        tex_name = f"{TEX_OUTPUT_DIR_REL_MAIN_PAPER}/{rel.with_suffix('.tex')}"
        lines.append(f"\\input{{{tex_name}}}")
    lines.append(r"")
    return "\n".join(lines)


def run_stylelint(css_path: str) -> list[LintError]:  # noqa: C901
    """Runs stylelint on a CSS file and returns LintErrors. Returns empty list if stylelint isn't available or config is missing."""
    try:
        result = subprocess.run(  # noqa: S603
            ["npx", "stylelint", "--formatter", "json", css_path],  # noqa: S607
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        print("  ⚠ npx not found, skipping stylelint")
        return []

    # stylelint exits 2 on lint errors, 1 on fatal/config error
    if result.returncode == 1:
        print(f"  ⚠ stylelint config/fatal error: {result.stderr.strip()}")
        return []

    try:
        data = json.loads(result.stderr)
    except json.JSONDecodeError:
        print("  ⚠ stylelint returned unparseable output")
        return []

    errors: list[LintError] = []
    for file_result in data:
        for warning in file_result.get("warnings", []):
            text = warning["text"]
            rule = warning["rule"]
            text = text.removesuffix(f" ({rule})")
            errors.append(
                LintError(
                    line=warning["line"],
                    message=f"[stylelint] {rule}: {text}",
                ),
            )
    return errors


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:  # noqa: C901
    os.makedirs(MD_OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEX_OUTPUT_DIR, exist_ok=True)

    print("── Resolving files...")
    css_files = resolve_files()
    if not css_files:
        print("  ✗ No CSS files matched. Check your INCLUDE/EXCLUDE config.")
        sys.exit(1)
    print(f"  ✓ {len(css_files)} file(s) to process:")
    for f in css_files:
        print(f"    {f}")

    processed: list[str] = []

    for css_path in css_files:
        if not os.path.isfile(css_path):
            print(f"  ✗ File not found, skipping: {css_path}")
            continue

        print(f"\n── Processing: {css_path}")
        roots, lint_errors = parse_css(css_path)
        stylelint_errors = run_stylelint(css_path)
        lint_errors = sorted(lint_errors + stylelint_errors, key=lambda e: e.line)

        if lint_errors:
            print(f"  ⚠ {len(lint_errors)} lint issue(s):")
            for err in lint_errors:
                print(f"    line {err.line}: {err.message}")
        else:
            print("  ✓ No lint issues")

        # markdown
        md_content = generate_md(css_path, roots, lint_errors)
        rel = Path(css_path).relative_to(ROOT_FOLDER)  # → fonts/comic-mono.css
        md_out_path = Path(MD_OUTPUT_DIR) / rel.with_suffix(".md")
        md_out_path.parent.mkdir(parents=True, exist_ok=True)
        Path(md_out_path).write_text(md_content, encoding="utf-8")
        print(f"  ✓ MD  → {md_out_path}")

        # latex
        tex_content = generate_tex(css_path, roots, lint_errors)
        tex_out_path = Path(TEX_OUTPUT_DIR) / rel.with_suffix(".tex")
        tex_out_path.parent.mkdir(parents=True, exist_ok=True)
        Path(tex_out_path).write_text(tex_content, encoding="utf-8")
        print(f"  ✓ TEX → {tex_out_path}")

        processed.append(css_path)

    if not processed:
        print("\nNo CSS files were successfully processed.")
        sys.exit(1)

    # index files
    print("\n── Generating index files...")

    md_index_path = os.path.join(MD_OUTPUT_DIR, "README.md")
    Path(md_index_path).write_text(
        generate_md_index(processed, MD_OUTPUT_DIR),
        encoding="utf-8",
    )
    print(f"  ✓ MD  index → {md_index_path}")

    tex_index_path = os.path.join(TEX_OUTPUT_DIR, "index.tex")
    Path(tex_index_path).write_text(
        generate_tex_index(processed, TEX_OUTPUT_DIR),
        encoding="utf-8",
    )
    print(f"  ✓ TEX index → {tex_index_path}")

    print(f"\n── Done! Processed {len(processed)} file(s).")


if __name__ == "__main__":
    main()
