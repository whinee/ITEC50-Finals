# TODO

## Documentation

- [ ] Automated Lighthouse Reports
- [ ] Automated Python Docs generator for MD and LaTeX

## Paper

- [ ] Adhere to the format given

## Scripts

- [ ] Add functionality to generate bookmarks, tags, and JD IDs that has date from Unix Epoch until the current datetime

## Fullstack

- [ ] Add functionality to get instantaneous feedback from users thru the hamburger menu

## Backend

- [ ] Add auto-provisioning of a demo account to a user in demo mode
- [ ] [TEST] Fix authorized pages so that they shall be inacessible when a lingering token is used for a user that no longer exist in the database
- [ ] Fix HTTP Exceptions to be flash messages where necessary
- [ ] Add SMTP server for 2FA and E-mail verification
- [ ] Add Captcha, TOTP/MFA, and rate limiting to the following endpoints:
  - [ ] `/auth/login`
  - [ ] `/auth/register`
- [ ] Add SSO and OIDC authentication
- [ ] Add zero-trust encryption
- [ ] Add API token authentication

## Frontend

- [ ] Fix goofy favicons to have squashed/flattened transforms
- [ ] Add functionality to let users pick tags' color
- [ ] Add background color per foreground color
- [ ] Add the ability for users to pick from preset color schemes or make their own and be able to share it with other users, either thru a marketplace, or thru sharing a code
- [ ] Add functionality to generate usernames in the frontend by hitting the backend endpoint
- [ ] Fix `.erase-input` appearing as a white button
- [ ] Add functionality to view passwords as clear text in input
- [x] Add comprehensive sectioning/comment to the stylesheets
- [x] Fix y-overflow issue, presumably due to the ever-so-present hamburger menu
- [x] Fix time to be converted from UTC to local time when displayed in the frontend
- [x] Fix frontend to show a skeleton instead of a zero or blank screen when the data is still loading

## E2E Testing

- [ ] Test modals

## Deployment

- [ ] Run `scripts/seed.py` every hour to clear the database of user inputs.
