"""Security Hardening Constants.

Globally defined cryptographic expiration lifetimes. These hardcoded values ensure that session tokens (`JWT`) and symmetric cookie payloads expire aggressively, drastically narrowing the attack window for hijacked sessions.
"""

JWT_EXPIRES_AFTER = 60 * 60 * 7
COOKIE_EXPIRES_AFTER = 60 * 60 * 24
