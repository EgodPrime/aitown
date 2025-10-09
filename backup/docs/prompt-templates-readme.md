Prompt Templates (docs/prompt-templates.json)

This project includes a small, curated prompt template library used by the NPC creation/editing UI.

Location
- `docs/prompt-templates.json` — read-only JSON array of plain-text prompt snippets (one array of strings).

How to extend
1. Edit `docs/prompt-templates.json` and add or modify entries. Each entry should be a short plain-text hint (<= 500 characters) focused on NPC behavior (no API keys or secrets).
2. Commit the change to the repository. For this release, the server loads the templates into memory at startup and watches the file for changes; updated files will be reloaded automatically in development (simple file watch). In some production environments file watching may be disabled; restart the server if you don't see updates.

Future improvements
- Templates are loaded into memory at startup and watched for changes (see `src/config/promptTemplates.ts`).
- Provide an admin-only API to manage templates (create/update/delete) and persist into a database or config.
- Add localization support and structured template metadata (id, locale, description).
