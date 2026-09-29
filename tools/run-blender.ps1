# Forward Blender arguments unchanged; do not add a param block (Blender uses -b, -P, etc.).
$ErrorActionPreference = 'Stop'
$blenderArgs = $args

# Blender 5.2.1 uses this Windows API for its thumbnail cache and ignores failure.
# USERPROFILE/HOME overrides do not fix that code path.
if (-not ('Constellation.BlenderProfile' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Text;
using System.Runtime.InteropServices;
namespace Constellation {
    public static class BlenderProfile {
        [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool SHGetSpecialFolderPathW(
            IntPtr hwnd, StringBuilder path, int folder, bool create);
    }
}
'@
}
$profileBuffer = [Text.StringBuilder]::new(260)
$profileOk = [Constellation.BlenderProfile]::SHGetSpecialFolderPathW(
    [IntPtr]::Zero, $profileBuffer, 0x28, $false)
$profilePath = $profileBuffer.ToString()
if (-not $profileOk -or [string]::IsNullOrWhiteSpace($profilePath) -or
    -not [IO.Path]::IsPathRooted($profilePath) -or
    -not (Test-Path -LiteralPath $profilePath -PathType Container)) {
    throw 'Blender blocked: Windows profile lookup failed. This environment causes corrupt thumbnail folders. Use an approved normal-user execution context; do not invoke blender.exe directly or disable the sandbox globally.'
}

$blenderExe = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
if (-not (Test-Path -LiteralPath $blenderExe -PathType Leaf)) {
    throw "Blender executable not found: $blenderExe"
}
& $blenderExe @blenderArgs
exit $LASTEXITCODE
