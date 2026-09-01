#Requires -Version 7.0
<#
build.ps1 - Desktop build entry: frontend -> backend sidecar -> Tauri shell/NSIS.

WHY THIS SCRIPT EXISTS
  tauri.conf.json declares `bundle.resources: { "../../dist/alas-backend": "alas-backend" }`.
  That path is the PyInstaller onedir backend sidecar (dist/alas-backend/alas-backend.exe).
  tauri-build validates resource paths at compile time, so `cargo build --release`
  (and `pnpm tauri build`) fails with
      resource path `..\..\dist\alas-backend` doesn't exist
  unless the sidecar was built first. This script enforces that order (the same
  order the CI release workflow uses), so nobody has to rediscover it.

Usage (run from the repo root; pwsh 7+ required):
  pwsh deploy/packaging/build.ps1                       # frontend + sidecar + NSIS installer
  pwsh deploy/packaging/build.ps1 -ShellOnly            # frontend + sidecar + cargo build --release
  pwsh deploy/packaging/build.ps1 -SkipFrontend -ShellOnly   # sidecar (if needed) + cargo build --release
#>
[CmdletBinding()]
param(
    # Skip `pnpm install` + `pnpm build` in webapp-tauri (use when dist/ is fresh).
    [switch]$SkipFrontend,
    # Compile the shell only (cargo build --release) instead of the NSIS bundle.
    [switch]$ShellOnly
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$frontendDir = Join-Path $repo 'webapp-tauri'
$sidecar = Join-Path $repo 'dist\alas-backend'
$sidecarExe = Join-Path $sidecar 'alas-backend.exe'

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Error "pyinstaller not found. Install it with: uv tool install 'pyinstaller>=6.19'"
}

# 1) Frontend SPA: the sidecar embeds webapp-tauri/dist (backend serves it), and
#    the shell's frontendDist points at ../dist as well.
if (-not $SkipFrontend) {
    Write-Host "==> Building frontend (webapp-tauri): pnpm install + pnpm build"
    Push-Location $frontendDir
    try {
        pnpm install --frozen-lockfile
        pnpm build
    } finally {
        Pop-Location
    }
} else {
    Write-Host "==> Skipping frontend build (-SkipFrontend)"
}

# 2) Backend sidecar: required by tauri-build's resource check before the shell
#    can compile (see header). Rebuild it by deleting dist/alas-backend.
if (Test-Path $sidecarExe) {
    Write-Host "==> Sidecar already present: $sidecar (delete the folder to rebuild)"
} else {
    Write-Host "==> Building backend sidecar with PyInstaller (a few minutes) -> $sidecar"
    Push-Location $repo
    try {
        pyinstaller --clean --noconfirm deploy/packaging/alas_backend.spec
    } finally {
        Pop-Location
    }
    if (-not (Test-Path $sidecarExe)) {
        Write-Error "PyInstaller finished but $sidecarExe is missing; check the spec output."
    }
}

# 3) Shell: plain compile, or full NSIS bundle (same step the CI runs).
if ($ShellOnly) {
    Write-Host "==> Compiling shell: cargo build --release (src-tauri)"
    Push-Location (Join-Path $frontendDir 'src-tauri')
    try {
        cargo build --release
    } finally {
        Pop-Location
    }
} else {
    Write-Host "==> Bundling NSIS installer: pnpm tauri build (webapp-tauri)"
    Push-Location $frontendDir
    try {
        pnpm tauri build
    } finally {
        Pop-Location
    }
}

Write-Host "Done."
