# Presentation Preparation Tasks

## Goal

Finish DeciMark for Tuesday panel defense with minimum risk.

Primary target: stable demo, clean paper, documented decisions, backup plans.

## Operating Rule

Scope freeze until defense is done.

Allowed work:

- bug fixes
- documentation
- proofing
- deployment checks
- paper finalization
- demo rehearsal
- backup creation

Not allowed:

- new features
- major refactors
- speculative polish with no presentation value

## Priority Order

1. Live app reliability
1. Paper accuracy
1. Defense explanation
1. Backup paths
1. Extra polish only if time remains

______________________________________________________________________

## 🧍‍♀️ Lyra's Tasks

### Workstream 1 — Deployment

- [ ] Confirm production environment variables
- [ ] Confirm database migrations run cleanly
- [ ] Confirm Postgres and Redis available on deploy target
- [ ] Confirm static assets load in prod
- [ ] Confirm login, logout, and bookmark CRUD work in live environment
- [ ] Confirm no hardcoded localhost URLs remain
- [ ] Confirm backup and rollback command is documented
- [ ] Confirm deployment instructions are current in docs and paper

*Done when: Live site opens without errors, main user flow works end to end, recovery path exists if deploy breaks.*

### Workstream 5 — Panel Defense Prep

- [ ] Prepare 3-minute project summary
- [ ] Prepare 5-minute full demo summary
- [ ] Prepare architecture explanation
- [ ] Prepare database schema explanation
- [ ] Prepare deployment explanation
- [ ] Prepare technology choice rationale
- [ ] Prepare limitations and future work
- [ ] Prepare likely panel questions
- [ ] Prepare short answers for each question

**Suggested panel questions:**

- Why this project?
- What problem does it solve?
- Why this stack?
- Why not a SPA?
- Why Hypercorn?
- Why PostgreSQL?
- Why Jinja2 and vanilla JS?
- What is the data model?
- How does deployment work?
- What is future work after submission?

*Done when: Answers fit time limit, answers are consistent with paper and code, no improvisation needed for core questions.*

### Workstream 6 — Backup Plan

- [ ] Save final paper PDF locally
- [ ] Save final project zip or repo snapshot
- [ ] Save deployment notes offline
- [ ] Save demo account credentials securely
- [ ] Save screenshots of key pages
- [ ] Save a local run command cheat sheet
- [ ] Prepare fallback if internet fails
- [ ] Prepare fallback if server fails

*Done when: Presentation can continue even if live server breaks.*

### Workstream 7 — Timeline

**Sunday night**

- Freeze scope
- Capture remaining issues
- Start doc cleanup
- Draft deployment + defense notes

**Monday**

- Finalize docs and paper
- Run lint and report generation
- Fix any remaining errors
- Deploy and verify live environment

**Monday night**

- Rehearse demo
- Rehearse panel answers
- Generate final PDFs and backups
- Stop editing early

**Tuesday before panel**

- Open live app
- Check one full demo path
- Bring backups
- Deliver with no surprise edits

______________________________________________________________________

## 🤖 AI's Tasks (Gemini)

### Workstream 2 — Paper Finalization

- [ ] Proofread all sections for grammar and tone
- [ ] Remove unsupported claims and contradictions
- [ ] Verify citations against `paper/refs.bib`
- [ ] Verify captions, figure labels, and cross-references
- [x] Document architecture accurately
- [x] Document database schema accurately
- [x] Document deployment steps accurately
- [x] Document tech stack rationale accurately
- [x] Update recommendations section with real future plans
- [x] Ensure AI disclosure matches actual usage
- [x] Export final PDF and inspect layout

*Done when: Paper reflects actual implementation, no stale claims remain, PDF compiles cleanly, print copy is ready.*

### Workstream 3 — README and Docs Sync

- [x] Update `docs/README.md` to match real `just` recipes
- [x] Update `docs/README.md` to explain ALL environment variables in .env.example
- [x] Add concise dependency rationale
- [x] Remove stale or unsupported setup instructions
- [x] Update `docs/TODO.md` to current scope
- [x] Add recommendations summary to project docs if needed
- [x] Document `justfile` recipes in human-readable form
- [x] Keep deployment instructions consistent across docs and paper

*Done when: Docs agree with current codebase, no obsolete commands mentioned, no duplicated instructions across files.*

### Workstream 4 — Justfile Documentation

- [x] Document public recipes
- [x] Mark private helper recipes as internal
- [x] Note external tool requirements for lint recipes
- [x] Note Docker Compose dependency for dev/run recipes
- [x] Call out missing recipes mentioned in docs if they remain absent
- [x] Keep naming consistent with recipe names in `justfile`

*Done when: Reader can tell what each recipe does without opening the file.*

### Workstream 8 — Code Fixes (Ruff)

- [x] Fix `D103` and `D401` Ruff errors in `main.py`
- [x] Fix `D103` and `D401` Ruff errors in `scripts/*.py`

## Success Criteria

The project is ready when all of these are true:

- live app works
- paper compiles cleanly
- paper matches codebase
- docs match actual commands
- demo path is rehearsed
- backups exist
- panel answers are prepared

## Working Rule for This Project

If something does not help Tuesday's presentation, it waits.
