# Blender thumbnail folder incident (2026-09-23)

## Cause

Installed Blender: 5.2.1 LTS, build 9e2066aef7ef.
In `source/blender/imbuf/intern/thumbs.cc`, Windows `get_thumb_dir()` declares
an uninitialized `wchar_t dir_16[MAX_PATH]`, calls `SHGetSpecialFolderPathW`
for `CSIDL_PROFILE`, then converts the buffer without checking the return value.
Source: https://raw.githubusercontent.com/blender/blender/blender-v5.2-release/source/blender/imbuf/intern/thumbs.cc

On this machine, a read-only API probe returned false under
`DESKTOP-HL6LOKE\CodexSandboxOffline` and true with `C:\Users\User` under
`DESKTOP-HL6LOKE\User`. The environment variable USERPROFILE was already correct
in the failing context. A factory-startup background save reproduced the
OpenImageIO thumbnail write failure without loading any project asset.

This explains the random Unicode cache directories and the UTF-16 byte pairs
that decode to pieces of recently used texture paths. It is an unchecked API
failure in Blender exposed by the execution account, not renamed asset folders.

## Project mitigation

Run CLI jobs through `tools/run-blender.ps1`. It checks the same Windows API and
refuses to start Blender if the lookup fails. A normal-user run must use the
execution tool's approval mechanism. This does not patch the installed Blender
binary or intercept callers that ignore the launcher.

Example from the project root:

```powershell
& ./tools/run-blender.ps1 --background --factory-startup --python-exit-code 1 --python-expr "import bpy; bpy.ops.wm.save_as_mainfile(filepath='C:/Users/User/Documents/UnrealProjects/Constellation/Saved/BlenderProfileCheck/probe.blend')"
```

Expected: the restricted context stops before Blender launches; an approved
normal-user context saves successfully without thumbnail errors or new corrupt
directories. Use `Saved/BlenderProfileCheck` only for disposable diagnostic output.

Do not work around this by changing locale, setting HOME/XDG_CACHE_HOME, hiding
the directories in gitignore, or repeatedly deleting them. Windows thumbnail
lookup in this Blender code does not use those environment variables.

## Validation on 2026-09-23

- Direct sandboxed factory-startup save: thumbnail write failure reproduced.
- Guarded sandboxed launch: exited with profile-lookup error before Blender ran.
- Approved normal-user guarded launch: exit 0, saved the diagnostic blend file,
  no thumbnail error and no new project-root directories.
- Removed 16 recurring directories after checking each contained only the four
  empty thumbnail-cache directories; remaining abnormal root directories: 0.
- PowerShell launcher parsed without errors. Existing interactive Blender was
  left running.
