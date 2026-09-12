# Windows PowerShell Installer for gemini-agent-team plugin
# Strictly English only. No icons or emojis.

[CmdletBinding()]
param(
    [string]$TargetDir = "$HOME\.gemini\config\plugins\agent-team",
    [switch]$SkipDoctor
)

$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/Kaivian/gemini-agent-team.git"
$ConfigFile = Join-Path $HOME ".gemini\config\config.json"

Write-Host "=================================================="
Write-Host "Gemini Agent Team Plugin: Windows Installer"
Write-Host "Target Directory: $TargetDir"
Write-Host "=================================================="

# --------------------------------------------------
# Step 1: Prerequisite Verification
# --------------------------------------------------
Write-Host "[1/4] Verifying system prerequisites..."

# 1a. Check Git
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Error "[FAIL] Git CLI is not installed or not in system PATH. Please install Git from https://git-scm.com/ and rerun."
    exit 1
}
$gitVer = (git --version).Trim()
Write-Host "  [PASS] Git: $gitVer"

# 1b. Check Python (>= 3.10)
$pythonExe = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
}

if (-not $pythonExe) {
    Write-Error "[FAIL] Python 3 is not installed or not in system PATH. Please install Python 3.10+ from https://www.python.org/ and rerun."
    exit 1
}

$pyCheckCode = "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'); sys.exit(0 if sys.version_info >= (3, 10) else 1)"
$pyVersionOutput = & $pythonExe -c $pyCheckCode
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Python version ($pyVersionOutput) is below the minimum required version 3.10. Please install Python 3.10 or higher."
    exit 1
}
Write-Host "  [PASS] Python: $pyVersionOutput (>= 3.10)"

# --------------------------------------------------
# Step 2: Repository Deployment
# --------------------------------------------------
Write-Host "[2/4] Deploying repository..."
$resolvedTarget = [System.IO.Path]::GetFullPath($TargetDir)
$currentDir = (Get-Location).Path
$resolvedCurrent = [System.IO.Path]::GetFullPath($currentDir)

$isSameDirectory = ($resolvedCurrent.TrimEnd('\') -ieq $resolvedTarget.TrimEnd('\'))

if (Test-Path (Join-Path $resolvedTarget ".git")) {
    Write-Host "  Updating existing Git repository at $resolvedTarget..."
    try {
        git -C $resolvedTarget pull --ff-only
        Write-Host "  [PASS] Repository updated successfully."
    } catch {
        Write-Warning "  [WARN] Git pull encountered an error. Retaining local files."
    }
} elseif ($isSameDirectory) {
    Write-Host "  Installer running from within target directory ($resolvedTarget). Skipping clone."
    Write-Host "  [PASS] Using local working tree."
} elseif (Test-Path $resolvedTarget) {
    Write-Host "  Directory already exists at $resolvedTarget without .git tracking."
    Write-Host "  [PASS] Preserving existing directory files."
} else {
    Write-Host "  Cloning repository into $resolvedTarget..."
    $parentDir = Split-Path -Parent $resolvedTarget
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }
    git clone $RepoUrl $resolvedTarget
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[FAIL] Failed to clone repository from $RepoUrl."
        exit 1
    }
    Write-Host "  [PASS] Repository cloned successfully."
}

# --------------------------------------------------
# Step 3: Configure ~/.gemini/config/config.json
# --------------------------------------------------
Write-Host "[3/4] Configuring Gemini plugin registry..."
$configDir = Split-Path -Parent $ConfigFile
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$updateConfigScript = @"
import json
from pathlib import Path

config_path = Path(r'$ConfigFile')
if config_path.exists():
    try:
        data = json.loads(config_path.read_text(encoding='utf-8'))
    except Exception:
        data = {}
else:
    data = {}

if not isinstance(data, dict):
    data = {}

if 'plugins' not in data or not isinstance(data['plugins'], dict):
    data['plugins'] = {}

if 'agent-team' not in data['plugins'] or not isinstance(data['plugins']['agent-team'], dict):
    data['plugins']['agent-team'] = {}

data['plugins']['agent-team']['enabled'] = True

config_path.parent.mkdir(parents=True, exist_ok=True)
config_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
"@

& $pythonExe -c $updateConfigScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "[FAIL] Failed to update plugin configuration in $ConfigFile."
    exit 1
}
Write-Host "  [PASS] Enabled agent-team plugin in $ConfigFile"

# --------------------------------------------------
# Step 4: Run Doctor Diagnostics
# --------------------------------------------------
if ($SkipDoctor) {
    Write-Host "[4/4] Skipping doctor diagnostics as requested."
} else {
    Write-Host "[4/4] Running system and plugin diagnostics..."
    $doctorPath = Join-Path $resolvedTarget "scripts\doctor.py"
    if (-not (Test-Path $doctorPath)) {
        $doctorPath = Join-Path $resolvedCurrent "scripts\doctor.py"
    }

    if (Test-Path $doctorPath) {
        & $pythonExe $doctorPath
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "[WARN] Diagnostics completed with one or more non-blocking warnings."
        } else {
            Write-Host "  [PASS] Diagnostics completed successfully."
        }
    } else {
        Write-Warning "[WARN] Diagnostic script not found at $doctorPath."
    }
}

# --------------------------------------------------
# Installation Summary and Next Steps
# --------------------------------------------------
Write-Host ""
Write-Host "=================================================="
Write-Host "Installation Complete: Gemini Agent Team Plugin"
Write-Host "=================================================="
Write-Host "Plugin Path: $resolvedTarget"
Write-Host "Config Path: $ConfigFile (plugins.agent-team.enabled = true)"
Write-Host ""
Write-Host "Next Steps & Usage:"
Write-Host "1. Antigravity & Gemini CLI:"
Write-Host "   Run: /agent-team `"Your task description here`""
Write-Host ""
Write-Host "2. Claude Code Marketplace Catalog:"
Write-Host "   Path: $resolvedTarget\.claude-plugins\marketplace.json"
Write-Host ""
Write-Host "3. Diagnostics Utility:"
Write-Host "   Run: python $resolvedTarget\scripts\doctor.py"
Write-Host "=================================================="
