import sys

md_content = sys.stdin.read().strip().split('\n')
tex_lines = [
    r"\begin{table}[H]",
    r"  \centering",
    r"  \begin{tabular}{|l|l|c|}",
    r"  \hline",
    r"  \textbf{Test File} & \textbf{Function} & \textbf{Status} \\",
    r"  \hline"
]

for line in md_content:
    if not line.startswith('|') or 'filepath' in line or '---' in line or 'TOTAL' in line:
        continue
    parts = [p.strip() for p in line.split('|')[1:-1]]
    if len(parts) >= 3:
        filepath = parts[0].replace('_', r'\_')
        func = parts[1].replace('_', r'\_')
        status = r"\textcolor{green}{Passed}" if int(parts[2]) > 0 else r"\textcolor{red}{Failed}"
        tex_lines.append(f"  \\texttt{{{filepath}}} & \\texttt{{{func}}} & {status} \\\\")
        tex_lines.append(r"  \hline")

tex_lines.extend([
    r"  \end{tabular}",
    r"  \caption{Automated E2E Testing Suite Results.}",
    r"  \label{tab:e2e-test-results}",
    r"\end{table}"
])

with open('paper/e2e_test_table.tex', 'w') as f:
    f.write('\n'.join(tex_lines) + '\n')
