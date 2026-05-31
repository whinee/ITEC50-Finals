# TODO

## Presentation Prep

- [ ] Align `paper/main.tex` with actual implementation
- [ ] Add deployment docs and recovery notes to paper
- [ ] Add database schema summary to paper
- [ ] Add dependency rationale to paper
- [ ] Remove repeated or unsupported claims from paper
- [ ] Verify citations and captions against `paper/refs.bib`
- [ ] Keep `docs/README.md`, `docs/TODO.md`, and paper command names in sync

## Docs

- [x] Replace stale setup commands in `docs/README.md`
- [x] Document public and private `justfile` recipes
- [x] Add concise stack rationale in `docs/README.md`
- [x] Document all environment variables from `.env.example` in `docs/README.md`
- [ ] Proofread docs for tone and contradictions

## Deployment

- [ ] Confirm production environment variables are documented
- [ ] Confirm migrations and rollback steps are documented
- [ ] Confirm Postgres and Redis dependency is documented
- [ ] Confirm backup and restore path is documented

## Testing

- [x] Run `just lint` cleanly
- [x] Run `just gen-reports` cleanly
- [ ] Recheck generated reports after doc edits

## Paper

- [ ] Add a dedicated recommendations section if still missing
- [ ] Confirm paper matches current command surface
- [ ] Confirm paper matches current data model
