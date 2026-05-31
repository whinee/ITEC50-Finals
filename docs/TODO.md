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

## Backend

- [ ] Add zero-trust encryption
- [ ] Add API token authentication

## Frontend

- [ ] Add dedicated page for displaying all JD IDs and Tags
- [ ] Add dedicated page for displaying and editing a JD ID or a Tag
- [ ] Remove inline styles from Jinja2 templates
- [ ] [NO-AI] Fix goofy favicons to have 2D scale transforms
- [ ] Add background color per foreground color
- [ ] Add the ability for users to pick from preset color schemes or make their own and be able to share it with other users, either thru a marketplace, or thru sharing a code

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
