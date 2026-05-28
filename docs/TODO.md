# TODO

## Documentation

- [ ] Automated Lighthouse Reports
- [x] Automated Python Docs generator for MD and LaTeX
- [ ] Fix python docstrings
- [x] Document .env variables

## Paper

- [x] Adhere to the format given
- [ ] Mention in the paper that the code embedded to the paper is not submitted, as the paper will be printed on a whole ream of paper if done so

## Scripts

- [x] Add functionality to generate bookmarks, tags, and JD IDs that has date from Unix Epoch until the current datetime

## Fullstack

- [ ] Add functionality to get instantaneous feedback from users thru the hamburger menu using a feedback form
- [ ] Fix JDNodes not being connected to each other
- [ ] Add enable/disable flags for different OAuth clients in .env file

## Backend

- [x] Add auto-provisioning of a demo account to a user in demo mode
- [x] Fix authorized pages so that they shall be inacessible when a lingering token is used for a user that no longer exist in the database
- [x] Fix HTTP Exceptions to be flash messages where necessary
- [ ] Add SMTP server for 2FA and E-mail verification
- [ ] Add Captcha, TOTP/MFA, and rate limiting to the following endpoints:
  - [ ] `/auth/login`
  - [ ] `/auth/register`
- [ ] Add SSO and OIDC authentication
- [ ] Add zero-trust encryption
- [ ] Add API token authentication

## Frontend

- [ ] Add dedicated page for displaying all JD IDs and Tags
- [ ] Add dedicated page for displaying and editing a JD ID or a Tag
- [ ] Remove inline styles from Jinja2 templates
- [ ] [NO-AI] Fix goofy favicons to have 2D scale transforms
- [x] Add functionality to let users pick tags' color
- [ ] Add background color per foreground color
- [ ] Add the ability for users to pick from preset color schemes or make their own and be able to share it with other users, either thru a marketplace, or thru sharing a code
- [x] Add functionality to generate usernames in the frontend by hitting the backend endpoint
- [x] Fix `.erase-input` appearing as a white button
- [x] Add functionality to view passwords as clear text in input
- [x] Add comprehensive sectioning/comment to the stylesheets
- [x] Fix y-overflow issue, presumably due to the ever-so-present hamburger menu
- [x] Fix time to be converted from UTC to local time when displayed in the frontend
- [x] Fix frontend to show a skeleton instead of a zero or blank screen when the data is still loading

## Testing

- [x] Test modals

## Deployment

- [ ] Run `scripts/seed.py` every hour to clear the database of user inputs.
