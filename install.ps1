# Thin wrapper; shared implementation validates before changing host config.
[CmdletBinding()]
param(
    [ValidateSet('codex', 'gemini')][string]$HostName = 'codex',
    [string]$TargetDir,
    [string]$ConfigFile,
    [string]$SkillsDir,
    [string]$CodexHome,
    [switch]$Update,
    [switch]$SkipDoctor
)
$ErrorActionPreference = 'Stop'
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) { $pythonCommand = Get-Command py -ErrorAction SilentlyContinue }
if (-not $pythonCommand) { throw 'Python 3.10 or newer is required.' }
$installArgs = @((Join-Path $PSScriptRoot 'scripts/install_plugin.py'), '--host', $HostName)
foreach ($pair in @(@('--target-dir', $TargetDir), @('--config-file', $ConfigFile), @('--skills-dir', $SkillsDir), @('--codex-home', $CodexHome))) {
    if ($pair[1]) { $installArgs += $pair }
}
if ($Update) { $installArgs += '--update' }
if ($SkipDoctor) { $installArgs += '--skip-doctor' }
& $pythonCommand.Source @installArgs
exit $LASTEXITCODE
