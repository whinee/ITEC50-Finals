echo "\section{Automated E2E Test Suite Results}

The complete pipeline execution of the end-to-end user interface and API testing suite generated the following results. This table verifies that all functional logic—ranging from authentication rate-limits to asynchronous DOM modifications—has passed regression tests against the final \texttt{1.0.0} release candidate.

\input{e2e_test_table.tex}

" > temp.tex
cat paper/e2e_screenshots.tex >> temp.tex
mv temp.tex paper/e2e_screenshots.tex
