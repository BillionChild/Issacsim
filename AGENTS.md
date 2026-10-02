# Project instructions

## Scope and workflow
- Engine warehouse work lives in projects/engine-warehouse; editor host in exts/engine.warehouse. Use C:/IssacsimProject/Issacsim as the repository directory.
- Search -> partial read -> smallest change -> targeted validation. Preserve unrelated dirty files.
- Confirm new models/layout dimensions with the user before adopting them. Routine fixes within an approved design can proceed.
- Preserve original third-party assets. Keep generated assets, logs and reports in ignored external_assets/, logs/ and outputs/.
- This demo is kinematic with simulated vision. Do not claim physical validation or add mass/load checks unless requested.

## Context efficiency
- Check size before reading unfamiliar files. For files above 1 MB, use metadata/API queries first; never dump large USD, mesh, binary, texture or generated arrays into chat.
- Query USD with tools/inspect_usd.py (or a targeted pxr query); default to counts, bounds and the relevant subtree. Do not print full hierarchy or vertex/index arrays.
- Use rg to locate relevant functions before reading. Reuse unchanged findings; reread only changed regions or newly needed context.
- Capture noisy commands to logs/. Read relevant errors first with occurrence counts and a few surrounding lines; start with at most 50 lines, expand only for a specific question.
- Keep tool output around 1500 tokens per call where practical. Summarize large results on disk before returning them. Do not hide failures by truncating their only evidence.
- For long work, keep a short local audit: file sizes, full/partial/API reads, repeated-read reason, large output sources. This is an inspection audit, not exact token attribution.
- Use tools/token_usage_report.py for native usage by user turn. Cached input is part of input; reasoning is part of output. Never invent file/tool-level token counts, billing rates, or cache savings.
- Keep status notes concise and current. Do not load old transcripts or historical checkpoint appendices unless needed. Token conservation does not override correctness or required checks.

## Validation and stopping
- USD changes: verify affected prims, transforms, bindings/references and relevant physics schema only. No whole-repository validation by default.
- Visual optimization: preserve scale, bounds, UV/material assignments and grip/support geometry; make a separate candidate. Compare appearance and same-scene performance before adopting.
- Prefer offline checks. Keep the existing Isaac editor open; use Reload Code + Reset. Host/UI edits require extension off/on once. Launch an isolated integration test only when needed.
- Stop when relevant checks pass; broaden only for new failures or unresolved concerns. Report unverified runtime/visual results explicitly.
