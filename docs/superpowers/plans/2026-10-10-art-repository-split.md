# Art repository split execution
Approved design: optional private art repository plus self-contained game repository, develop only.
1. Copy the four unpublished authoring folders to constellation-art-source; compare every SHA256 and commit on develop.
2. Preserve unpublished game history in a local Git bundle; reconstruct only those unpublished commits, excluding copied authoring folders. Preserve unrelated working changes.
3. Store a pinned art commit, source hash mappings and integration evidence in docs/ArtPipeline. Keep original local files as ignored reimport copies.
4. Validate game assets without ArtSource directories using an isolated project root and cooked output. No claim of a full packaged playthrough.
5. Check LFS and diffs, push art and game develop without force, verify remote SHAs, then update Notion with both links and validation limits.
Review focus: no file loss, no unrelated ladder edit staged, no authoring files in unpublished game history, no required art checkout during cooking, no force push.
