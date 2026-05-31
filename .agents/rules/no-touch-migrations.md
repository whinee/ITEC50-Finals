---
trigger: always_on
glob:
description:
---

# Migrations Policy

## CRITICAL RULE: DO NOT TOUCH MIGRATION VERSIONS

You are strictly prohibited from **writing**, **editing**, **modifying**, or **creating** any files inside the `src/migrations/versions` directory.

- You may **read** these files to understand the database schema and history.
- You must **NEVER** edit them under any circumstances, even for documentation or docstring improvements.
