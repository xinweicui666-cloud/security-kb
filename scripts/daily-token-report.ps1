<#
.SYNOPSIS
    Claude Code Token Daily Report Generator
.DESCRIPTION
    Scans ~/.claude/projects JSONL session files, collects token usage for a given date,
    and generates a Markdown daily report.
.PARAMETER Date
    Target date in YYYY-MM-DD format. Defaults to today.
.PARAMETER OutputDir
    Report output directory. Defaults to ../reports/token-usage relative to script.
#>
param(
    [string]$Date = (Get-Date -Format 'yyyy-MM-dd'),
    [string]$OutputDir
)

$ErrorActionPreference = 'Continue'

# --- Config ---
$ClaudeDir = Join-Path $env:USERPROFILE '.claude'
$ProjectsDir = Join-Path $ClaudeDir 'projects'

if (-not $OutputDir) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $OutputDir = Join-Path (Split-Path -Parent $ScriptDir) 'reports\token-usage'
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}

# Model pricing (USD per 1M tokens)
$ModelPricing = @{
    'claude-sonnet-4-6'    = @{ Input = 3;    Output = 15 }
    'claude-sonnet-4-5'    = @{ Input = 3;    Output = 15 }
    'claude-opus-4-7'      = @{ Input = 15;   Output = 75 }
    'claude-opus-4-6'      = @{ Input = 15;   Output = 75 }
    'claude-haiku-4-5'     = @{ Input = 0.80; Output = 4 }
    'claude-haiku-4-5-20251001' = @{ Input = 0.80; Output = 4 }
    '360/glm-5.1'          = @{ Input = 0;    Output = 0 }
}

function Get-EstimatedCost {
    param([string]$Model, [long]$InputTokens, [long]$OutputTokens)
    $pricing = $ModelPricing[$Model]
    if (-not $pricing) {
        $pricing = @{ Input = 3; Output = 15 }
    }
    $inputCost = ($InputTokens / 1000000) * $pricing.Input
    $outputCost = ($OutputTokens / 1000000) * $pricing.Output
    return [math]::Round($inputCost + $outputCost, 4)
}

# --- Scan JSONL files ---
Write-Output "Scanning session files in $ProjectsDir ..."

$jsonlFiles = Get-ChildItem -Path $ProjectsDir -Filter '*.jsonl' -Recurse -File
Write-Output "Found $($jsonlFiles.Count) session files"

$records = @()

foreach ($file in $jsonlFiles) {
    $relativePath = $file.FullName.Substring($ProjectsDir.Length + 1)
    $projectName = $relativePath.Split('\')[0]

    $lines = Get-Content -Path $file.FullName -Encoding UTF8 -ErrorAction SilentlyContinue

    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }

        try {
            $obj = $line | ConvertFrom-Json -ErrorAction SilentlyContinue
        } catch {
            continue
        }

        if ($null -eq $obj) { continue }
        if ($obj.type -ne 'assistant') { continue }
        if ($null -eq $obj.message -or $null -eq $obj.message.usage) { continue }

        $ts = $obj.timestamp
        if ([string]::IsNullOrWhiteSpace($ts)) { continue }
        $msgDate = ($ts -split 'T')[0]
        if ($msgDate -ne $Date) { continue }

        $usage = $obj.message.usage
        $model = if ($obj.message.model) { $obj.message.model } else { 'unknown' }
        $sessionId = if ($obj.sessionId) { $obj.sessionId } else { 'unknown' }

        $inputT = [long]$usage.input_tokens
        $outputT = [long]$usage.output_tokens
        $totalT = [long]$usage.total_tokens
        if ($totalT -eq 0 -and ($inputT -gt 0 -or $outputT -gt 0)) {
            $totalT = $inputT + $outputT
        }

        $records += [PSCustomObject]@{
            InputTokens  = $inputT
            OutputTokens = $outputT
            TotalTokens  = $totalT
            Model        = $model
            SessionId    = $sessionId
            Project      = $projectName
            Timestamp    = $ts
        }
    }
}

Write-Output "Found $($records.Count) records for $Date"

# --- Aggregate ---
$totalInput = 0L
$totalOutput = 0L
$totalAll = 0L
$totalCost = 0.0

$byModel = @{}
$byProject = @{}
$bySession = @{}

foreach ($r in $records) {
    $totalInput += $r.InputTokens
    $totalOutput += $r.OutputTokens
    $totalAll += $r.TotalTokens
    $cost = Get-EstimatedCost -Model $r.Model -InputTokens $r.InputTokens -OutputTokens $r.OutputTokens
    $totalCost += $cost

    if (-not $byModel.ContainsKey($r.Model)) {
        $byModel[$r.Model] = @{ Input = 0L; Output = 0L; Total = 0L; Cost = 0.0 }
    }
    $byModel[$r.Model].Input += $r.InputTokens
    $byModel[$r.Model].Output += $r.OutputTokens
    $byModel[$r.Model].Total += $r.TotalTokens
    $byModel[$r.Model].Cost += $cost

    if (-not $byProject.ContainsKey($r.Project)) {
        $byProject[$r.Project] = @{ Total = 0L; Sessions = @{} }
    }
    $byProject[$r.Project].Total += $r.TotalTokens

    $sessionKey = "$($r.Project)|$($r.SessionId)"
    if (-not $bySession.ContainsKey($sessionKey)) {
        $bySession[$sessionKey] = @{
            Project   = $r.Project
            SessionId = $r.SessionId
            Model     = $r.Model
            Total     = 0L
            FirstTS   = $r.Timestamp
            LastTS    = $r.Timestamp
        }
    }
    $bySession[$sessionKey].Total += $r.TotalTokens
    if ($r.Timestamp -lt $bySession[$sessionKey].FirstTS) {
        $bySession[$sessionKey].FirstTS = $r.Timestamp
    }
    if ($r.Timestamp -gt $bySession[$sessionKey].LastTS) {
        $bySession[$sessionKey].LastTS = $r.Timestamp
    }

    if (-not $byProject[$r.Project].Sessions.ContainsKey($r.SessionId)) {
        $byProject[$r.Project].Sessions[$r.SessionId] = $true
    }
}

$activeSessions = $bySession.Count
$activeProjects = $byProject.Count

# --- Generate Markdown Report ---
$reportPath = Join-Path $OutputDir "$Date.md"
$now = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'

$lines = @()
$lines += "# Token Daily Report - $Date"
$lines += ""
$lines += "> Auto-generated at $now"
$lines += ""

# Summary
$lines += "## Summary"
$lines += ""
$lines += "| Metric | Value |"
$lines += "|--------|-------|"
$lines += "| Total Input Tokens | $totalInput |"
$lines += "| Total Output Tokens | $totalOutput |"
$lines += "| Total Tokens | $totalAll |"
$lines += "| Estimated Cost | `$$([math]::Round($totalCost, 2)) |"
$lines += "| API Calls | $($records.Count) |"
$lines += "| Active Sessions | $activeSessions |"
$lines += "| Active Projects | $activeProjects |"
$lines += ""

# By Model
$lines += "## By Model"
$lines += ""
$lines += "| Model | Input Tokens | Output Tokens | Total Tokens | Est. Cost |"
$lines += "|-------|-------------|--------------|-------------|----------|"
foreach ($model in ($byModel.Keys | Sort-Object)) {
    $m = $byModel[$model]
    $lines += "| $model | $($m.Input) | $($m.Output) | $($m.Total) | `$$([math]::Round($m.Cost, 4)) |"
}
$lines += ""

# By Project
$lines += "## By Project"
$lines += ""
$lines += "| Project | Total Tokens | Sessions |"
$lines += "|---------|-------------|----------|"
foreach ($proj in ($byProject.Keys | Sort-Object)) {
    $p = $byProject[$proj]
    $lines += "| $proj | $($p.Total) | $($p.Sessions.Count) |"
}
$lines += ""

# By Session
$lines += "## By Session"
$lines += ""
$lines += "| Session | Project | Model | Total Tokens | Time Range |"
$lines += "|---------|---------|-------|-------------|------------|"
foreach ($sk in ($bySession.Keys | Sort-Object { $bySession[$_].Total } -Descending)) {
    $s = $bySession[$sk]
    $shortId = $s.SessionId.Substring(0, [Math]::Min(8, $s.SessionId.Length)) + '...'
    $firstPart = ($s.FirstTS -split 'T')
    $lastPart = ($s.LastTS -split 'T')
    $firstTime = if ($firstPart.Length -gt 1) { $firstPart[1].Substring(0, [Math]::Min(8, $firstPart[1].Length)) } else { 'N/A' }
    $lastTime = if ($lastPart.Length -gt 1) { $lastPart[1].Substring(0, [Math]::Min(8, $lastPart[1].Length)) } else { 'N/A' }
    $lines += "| $shortId | $($s.Project) | $($s.Model) | $($s.Total) | $firstTime ~ $lastTime |"
}
$lines += ""

# Pricing Note
$lines += "## Pricing Reference"
$lines += ""
$lines += "Estimated cost based on (USD / 1M tokens):"
$lines += ""
$lines += "| Model | Input | Output |"
$lines += "|-------|-------|--------|"
$lines += "| claude-sonnet-4-6 | `$3 | `$15 |"
$lines += "| claude-opus-4-7 | `$15 | `$75 |"
$lines += "| claude-haiku-4-5 | `$0.80 | `$4 |"
$lines += "| 360/glm-5.1 | `$0 (internal) | `$0 (internal) |"
$lines += ""
$lines += "> Note: Estimated cost is for reference only. Actual cost per Anthropic Console."

$lines | Out-File -FilePath $reportPath -Encoding utf8
Write-Output "Report generated: $reportPath"