---
name: saps-search
description: Search SAPS clients and buildings by CPF/CNPJ or name, parse matches, and map spreadsheet rows without Vistar calls.
---

# SAPS targeted search

Use this repository only for authorized, read-only SAPS/SERTEN lookup.

1. Decide whether the source row requires a client or building search. Normalize CPF/CNPJ to digits and deduplicate unique keys before calling SAPS. For each key retain the lookup outcome and map cached results back to duplicate rows. Done when each input row has a lookup key or is marked unresolved.

2. Authenticate as the local operator. Run the CLI and enter that operator's own SAPS username and password at the prompts; use the local Bitwarden vault to retrieve the entry if needed. For an approved non-interactive runner, use an organization-approved secret injector and `--env-credentials`. Never put credentials/cookies in arguments, repository files, logs, chats, or sheets. Do not reuse another military member's account. Done when the authenticated search succeeds or access is reported as the blocker.

3. Use the direct search commands: `saps-search client --cnpj ...`, `client --name ...`, `client --redesim ...`, `building --cnpj ...`, or `building --name ...`. The client POST uses `_method=POST` and `data[Filter][filterFormId]=Cliente`; the building POST uses `_method=POST` and no `filterFormId`. Do not load the listing page first. Done when the response table is parsed or a status/auth/timeout error is recorded.

4. Prefer exact document comparison after removing punctuation. Retain every building row that matches. If no document is supplied, submit the full name once in uppercase and mark rows as candidates; the observed case/prefix behavior is an inference, and a name miss does not prove there is no record. Done when results are exact, candidate/ambiguous, no exact hit, or unresolved, with pagination indicated.

5. For batches, use a CSV with `target`, `cnpj_cpf`, and `name`; let the batch runner deduplicate and serialize. Client POSTs were observed at roughly 0.5–0.9 s; building POSTs at roughly 40 s to first byte. Keep the building timeout above that latency and do not fan out repeated searches. Done when each unique key has one recorded outcome.

6. Stop after returning requested lookup fields. Do not call `/serten/projetos/vistar` as a login preflight and do not follow action links. Process-status lookup is outside this repository's mapped routes. Done when no write/action or unverified detail route was used.
