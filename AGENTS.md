# Blender automation

For command-line Blender work in this project, invoke `tools/run-blender.ps1`
with the original Blender arguments instead of launching `blender.exe` directly.
This checks Windows profile lookup before Blender can create thumbnail caches.

Blender 5.2.1's thumbnail code does not check failure of
`SHGetSpecialFolderPathW(CSIDL_PROFILE)`. The Codex sandbox account on this machine
fails that call and Blender can create random Unicode directories containing
`.thumbnails` in its working directory. Setting HOME, USERPROFILE or XDG_CACHE_HOME
does not repair this Windows code path.

If the launcher reports profile lookup failure, use the tool's normal approval
mechanism to request an appropriate normal-user execution context for that specific
Blender job. Do not bypass the guard, change sandbox account permissions, or disable
the sandbox globally. Do not stop an existing interactive Blender session.

Diagnostic details and a regression check: `docs/blender-thumbnail-folders.md`.

# Character animation workflow

Before heroine animation, rigging, retargeting, or animation polishing work, read
`ArtSource/Heroine_Tripo_Review/AnimationWorkflow/SKILL.md`. It records the current
deliverables, preserved character style, contact/tempo/garment checks, Unreal
handoff steps, and lessons from retired drafts. Start from the maintained source
listed there, not removed intermediate versions.

# Modular environment production

Before modular environment asset production, concept-to-Unreal scene reconstruction,
or stairwell scene revisions, read `ArtSource/Stairwell_Modular/Workflow/SKILL.md`
and its `CURRENT.md`. They record the maintained playable map, reusable sources,
human review stages, character-scale-first checks, and cleanup rules. Use the
maintained sources rather than retired backup maps or one-off revision scripts.

For Tripo environment reconstruction, vegetation/water, reference matching, or
environment cleanup, also read `ArtSource/OvergrownHall/Workflow/README.md` and
`ArtSource/OvergrownHall/CURRENT.md`. They record the user-approved scene,
reusable lessons, source dependencies, and separate visual/play/performance checks.
