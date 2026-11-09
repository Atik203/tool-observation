<#
.SYNOPSIS
    Task runner for the tool-observation project (Windows PowerShell).

.DESCRIPTION
    Mirrors the Makefile targets. Defaults to the project's Python 3.12
    interpreter and falls back to `python` on PATH.

.EXAMPLE
    .\tasks.ps1 test
    .\tasks.ps1 setup
    .\tasks.ps1 validate
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('setup', 'test', 'lint', 'validate', 'compile', 'clean', 'help')]
    [string]$Task = 'help'
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
Push-Location $Root
try {
    $Preferred = 'C:\ProgramData\anaconda3\python.exe'
    if ($env:TOOLOBS_PYTHON) {
        $Python = $env:TOOLOBS_PYTHON
    }
    elseif (Test-Path $Preferred) {
        $Python = $Preferred
    }
    else {
        $Python = 'python'
    }

    function Invoke-Step {
        param([string]$Name, [scriptblock]$Block)
        Write-Host "==> $Name" -ForegroundColor Cyan
        & $Block
        if ($LASTEXITCODE -ne 0) {
            throw "$Name failed with exit code $LASTEXITCODE"
        }
    }

    switch ($Task) {
        'setup' {
            Invoke-Step 'Create/update conda environment' {
                conda env create -f environment.yml
                if ($LASTEXITCODE -ne 0) {
                    conda env update -f environment.yml --prune
                }
            }
            Invoke-Step 'Editable install with dev extras' {
                & $Python -m pip install -e ".[dev]"
            }
        }
        'test' {
            Invoke-Step 'pytest' { & $Python -m pytest -q }
        }
        'lint' {
            Invoke-Step 'ruff' { & $Python -m ruff check . }
        }
        'compile' {
            Invoke-Step 'compileall' { & $Python -m compileall -q src }
        }
        'validate' {
            Invoke-Step 'toolobs validate' { & $Python -m toolobs.cli validate }
        }
        'clean' {
            Invoke-Step 'Remove caches and build outputs' {
                $targets = @('.pytest_cache', '.ruff_cache', 'build', 'dist', 'src\tool_observation.egg-info')
                foreach ($t in $targets) {
                    if (Test-Path $t) { Remove-Item -Recurse -Force $t }
                }
                Get-ChildItem -Path $Root -Recurse -Directory -Filter '__pycache__' |
                    ForEach-Object { Remove-Item -Recurse -Force $_.FullName }
            }
            Write-Host 'Cleaned build and cache artifacts. Data directories were not touched.'
        }
        default {
            Write-Host 'tool-observation task runner'
            Write-Host 'Usage: .\tasks.ps1 <setup|test|lint|validate|compile|clean>'
            Write-Host 'Python: ' -NoNewline
            Write-Host $Python
        }
    }
}
finally {
    Pop-Location
}
