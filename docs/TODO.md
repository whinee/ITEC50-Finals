# TODO

## Documentation

- [ ] Automated Lighthouse Reports

## Paper

- [ ] Adhere to the format given

## Scripts

- [ ] Add functionality to generate bookmarks, tags, and JD IDs that has date from Unix Epoch until the current datetime

## Backend

- [ ] Convert HTTP Exceptions to flash messages where necessary
- [ ] Add SMTP server for 2FA and E-mail verification
- [ ] Add Captcha, TOTP/MFA, and rate limiting to the following endpoints:
  - [ ] `/auth/login`
  - [ ] `/auth/register`
- [ ] Add SSO and OIDC authentication

## Frontend

- [ ] Fix time to be converted from UTC to local time when displayed in the frontend
- [ ] Fix y-overflow issue, presumably due to the ever-so-present hamburger menu
- [ ] Add comprehensive sectioning/comment to the stylesheets
- [ ] Add background color per foreground color
- [ ] Add the ability for users to pick from preset color schemes or make their own and be able to share it with other users, either thru a marketplace, or thru sharing a code
- [ ] Add functionality to generate usernames in the frontend by hitting the backend endpoint
- [ ] Fix `.erase-input` appearing as a white button
- [ ] Add functionality to view passwords as clear text in input
