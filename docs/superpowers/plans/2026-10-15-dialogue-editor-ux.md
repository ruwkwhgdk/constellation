# Dialogue editor UX implementation plan

Goal: implement the approved usage navigation, key/content list, content-first editor, unified save and persistent local history/restore without changing game asset structures.

Constraints: no Clean/Rebuild, Intermediate deletion, competing build or new shared-checkout build. Preserve unrelated work. New native tests are written first but cannot be run until the coordinated build is available. Do not describe static checks as passing runtime tests.

- [x] Presentation model: deduplicate by actual source; hide only known identifier fields; group exact uses by asset/event; dynamic/package candidates remain diagnostics. Keep unknown usage explicit.
- [x] Save/history workflow: durable per-revision local journal, apply + asset save, failed-save retry, stale source checks, successful-history-only restore; preserve drafts on conflicts.
- [x] Slate UI: usage tree, key/content columns, content-first fixed editor/save, category controls, collapsed history and technical details; drafts survive selection/rescan and close cancellation.
- [ ] Tests: source identity vs equal text, exact vs dynamic grouping, history persistence, save failure/retry and restore conflict. Review and static validation; record unexecuted build/UI checks.

Files: TextManagementPresentation.{h,cpp}, TextManagementHistory.{h,cpp}, TextManagementUXTests.cpp; replace STextManagementPanel.cpp while preserving registration and invalidation hooks. Reuse TextManagementEditing primitives.


## Implementation and verification record
- Source changes implemented in the files above; no uasset, table schema, row ID, localization identity, build settings or Intermediate files were changed for this task. TextManagementEditing.cpp additionally rejects tab characters in category labels because the navigation hierarchy uses a tab separator internally.
- Exact usage groups are distinct from dynamic/package candidates. Known ST_StringData name fields in DT_SequenceStringData/DT_RegionStringData are hidden by default. Source-equivalent rows merge, equal wording with distinct sources does not.
- Unified Save retains the draft and original history Before value after cancellation/failure. The local journal is written before applying and only marked Saved after successful asset save. An interrupted journal stays unconfirmed. History strings use UTF-8 Base64 to preserve newlines, quotes and whitespace.
- Local history: Saved/StringManagementHistory/*.ini. Local panel widths: Saved/Config/StringManagementLayout.ini. Existing manual categories remain in Config/StringManagement.ini.
- History supports restoring either Before or After through the same save path; restores create new revisions. Only completed history records for the same target are eligible. Unrelated/external changes are not claimed as tracked history.
- Drafts survive selection/filter changes and refresh. Invisible items cannot remain active editing targets. Close offers save/discard/cancel. A pending in-memory applied save is explicitly distinguished from an unapplied draft.
- Static validation: delimiter balance, include existence against local UE5.8 headers, relevant Slate/FileManager/Config/Base64 API signatures and git diff --check. These checks do not establish successful native compilation or visual correctness.
- Read-only code review: selection reconciliation, localization-identity conflict recovery, and restore-dialog cancellation synchronization were corrected.
- **Not run:** native build, new automation tests, editor rendering/manual acceptance. No competing build was launched, even after transient process state could appear idle. Existing 2026-10-12 test results are not results for this change.

## Coordinated verification still required
- [ ] After the shared build owner coordinates access: normal incremental ConstellationEditor build (never Clean/Rebuild).
- [ ] Run Constellation.TextManagement including UX.UsageGrouping and UX.HistoryAndRetry. The new tests are written first but have not been executed.
- [ ] Verify: select 폐교/S0; key/content columns; no duplicate source rows; source/editor match when filters change; single Save updates disk; cancel/retry preserves draft; external identity/source conflict can reload; before/after restore writes a new revision; restart retains history; close dirty-draft choices; panel width persistence and readability at the user's window size.
- [ ] Verify file lock/read-only history directory and package save cancellation in the native editor. Tests simulate the asset-save I/O boundary; they do not replace a native disk-save acceptance check.
