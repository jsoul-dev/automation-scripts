# hosts-blocker.ps1
# General-purpose hosts file blocker
# Reads entries from hosts.txt next to this script
# Smart grouping: inserts near existing related entries, skips duplicates

$VERSION = "1.0.0"

# --- Self-elevate ---
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$hostsPath = "$env:windir\System32\drivers\etc\hosts"
$inputFile = Join-Path $PSScriptRoot "hosts.txt"

Write-Host
Write-Host "  hosts-blocker" -ForegroundColor Cyan
Write-Host

# --- Validate ---
if (-not (Test-Path $hostsPath)) {
    Write-Host "  Hosts file not found." -ForegroundColor Red
    pause; exit 1
}

if (-not (Test-Path $inputFile)) {
    Write-Host "  hosts.txt not found next to this script." -ForegroundColor Red
    Write-Host "  Create a hosts.txt with your entries, e.g.:" -ForegroundColor DarkGray
    Write-Host
    Write-Host "    # Filmora" -ForegroundColor DarkGray
    Write-Host "    127.0.0.1 platform.wondershare.com" -ForegroundColor DarkGray
    Write-Host "    127.0.0.1 api.wondershare.com" -ForegroundColor DarkGray
    Write-Host
    pause; exit 1
}

# --- Backup ---
$backupName = "hosts.backup." + (Get-Date -Format "yyyyMMdd_HHmmss")
$backupPath = Join-Path (Split-Path $hostsPath) $backupName
Copy-Item -LiteralPath $hostsPath -Destination $backupPath -ErrorAction SilentlyContinue
Write-Host "  Backup: $backupName" -ForegroundColor DarkGray

# --- Read current hosts file ---
$hostsLines = [System.IO.File]::ReadAllLines($hostsPath)
$existingDomains = @{}
foreach ($line in $hostsLines) {
    $trimmed = $line.Trim()
    if ($trimmed -and -not $trimmed.StartsWith('#')) {
        $parts = $trimmed -split '\s+', 2
        if ($parts.Count -eq 2) {
            $existingDomains[$parts[1].ToLower()] = $true
        }
    }
}

# --- Read input file ---
$inputLines = Get-Content $inputFile
$inputEntries = @()
foreach ($line in $inputLines) {
    $trimmed = $line.Trim()
    if ($trimmed) { $inputEntries += $trimmed }
}

if ($inputEntries.Count -eq 0) {
    Write-Host "  hosts.txt is empty." -ForegroundColor Yellow
    Write-Host; pause; exit 0
}

# --- Parse input into groups (header + entries) ---
$groups = @()
$currentHeader = $null
$currentEntries = @()

foreach ($entry in $inputEntries) {
    if ($entry.StartsWith('#')) {
        if ($currentEntries.Count -gt 0) {
            $groups += @{ Header = $currentHeader; Entries = $currentEntries }
        }
        $currentHeader = $entry
        $currentEntries = @()
    } else {
        $currentEntries += $entry
    }
}
if ($currentEntries.Count -gt 0) {
    $groups += @{ Header = $currentHeader; Entries = $currentEntries }
}

# --- Process each group ---
$totalSkipped = 0
$totalAdded = 0

foreach ($group in $groups) {
    $header = $group.Header
    $entries = $group.Entries

    $newEntries = @()
    $skipped = @()

    foreach ($entry in $entries) {
        $parts = $entry -split '\s+', 2
        if ($parts.Count -lt 2) { continue }
        $domain = $parts[1].ToLower()

        if ($existingDomains.ContainsKey($domain)) {
            $skipped += $domain
        } else {
            $newEntries += $entry
            $existingDomains[$domain] = $true
        }
    }

    $groupName = if ($header) { $header } else { "(no header)" }

    if ($skipped.Count -gt 0) {
        Write-Host
        Write-Host "  $groupName - Skipped ($($skipped.Count) already exist):" -ForegroundColor Yellow
        foreach ($s in $skipped) {
            Write-Host "    - $s" -ForegroundColor DarkGray
        }
    }

    if ($newEntries.Count -eq 0) { continue }

    $result = [System.Collections.Generic.List[string]]::new()
    $location = ""

    # --- Priority 1: Exact header match — merge into existing group (FIX for both bugs) ---
    $headerMatchIdx = -1
    if ($header) {
        for ($i = 0; $i -lt $hostsLines.Count; $i++) {
            if ($hostsLines[$i].Trim() -eq $header.Trim()) {
                $headerMatchIdx = $i
                break
            }
        }
    }

    if ($headerMatchIdx -ge 0) {
        # Find the last non-empty line of the existing block (stops at next header)
        $blockEnd = $headerMatchIdx
        for ($i = $headerMatchIdx + 1; $i -lt $hostsLines.Count; $i++) {
            $t = $hostsLines[$i].Trim()
            if ($t.StartsWith('#')) { break }
            if ($t -ne '') { $blockEnd = $i }
        }

        # Build insertion map: anchor line index -> ordered list of new entries to insert after it
        # Anchor = the last input-predecessor of each new entry that already exists in this block.
        # This preserves the input file's intended ordering even for "sandwiched" entries.
        $insertMap = @{}

        foreach ($newEntry in $newEntries) {
            # Find this entry's position in the input entries list
            $inputIdx = -1
            for ($q = 0; $q -lt $entries.Count; $q++) {
                if ($entries[$q] -eq $newEntry) { $inputIdx = $q; break }
            }

            $anchorLine = $blockEnd  # default: append to end of block
            $foundAnchor = $false

            # Walk backwards through the input to find the nearest predecessor
            # that already exists in the hosts block
            for ($j = $inputIdx - 1; $j -ge 0; $j--) {
                $prev = $entries[$j]
                if ($prev.StartsWith('#')) { continue }
                $prevParts = $prev -split '\s+', 2
                if ($prevParts.Count -lt 2) { continue }
                $prevDomain = $prevParts[1].ToLower()

                # Look for prevDomain within the existing block
                for ($k = $headerMatchIdx + 1; $k -lt $hostsLines.Count; $k++) {
                    $t = $hostsLines[$k].Trim()
                    if ($t.StartsWith('#')) { break }
                    if (-not $t) { continue }
                    $hp = $t -split '\s+', 2
                    if ($hp.Count -eq 2 -and $hp[1].ToLower() -eq $prevDomain) {
                        $anchorLine = $k
                        $foundAnchor = $true
                        break
                    }
                }
                if ($foundAnchor) { break }
            }

            if (-not $insertMap.ContainsKey($anchorLine)) {
                $insertMap[$anchorLine] = [System.Collections.Generic.List[string]]::new()
            }
            $insertMap[$anchorLine].Add($newEntry)
        }

        # Rebuild hosts with insertions applied highest-index-first to keep indices stable
        $result.AddRange([string[]]$hostsLines)
        $sortedKeys = $insertMap.Keys | Sort-Object -Descending
        foreach ($insertPoint in $sortedKeys) {
            $result.InsertRange($insertPoint + 1, $insertMap[$insertPoint].ToArray())
        }

        $location = "merged into existing group"

    } else {
        # --- Priority 2: Base-domain scan (original fallback logic) ---
        $baseDomains = @()
        foreach ($entry in $entries) {
            if (-not $entry.StartsWith('#')) {
                $p = $entry -split '\s+', 2
                if ($p.Count -eq 2) {
                    $domParts = $p[1].ToLower().Split('.')
                    if ($domParts.Count -ge 2) {
                        $base = $domParts[-2] + '.' + $domParts[-1]
                        if ($baseDomains -notcontains $base) { $baseDomains += $base }
                    }
                }
            }
        }

        $insertAfter = -1
        for ($i = 0; $i -lt $hostsLines.Count; $i++) {
            $hl = $hostsLines[$i].Trim()
            if ($hl -and -not $hl.StartsWith('#')) {
                $hp = $hl -split '\s+', 2
                if ($hp.Count -eq 2) {
                    $hdParts = $hp[1].ToLower().Split('.')
                    if ($hdParts.Count -ge 2) {
                        $hBase = $hdParts[-2] + '.' + $hdParts[-1]
                        if ($baseDomains -contains $hBase) { $insertAfter = $i }
                    }
                }
            }
        }

        if ($insertAfter -ge 0) {
            for ($i = 0; $i -le $insertAfter; $i++) { $result.Add($hostsLines[$i]) }
            foreach ($ne in $newEntries) { $result.Add($ne) }
            for ($i = $insertAfter + 1; $i -lt $hostsLines.Count; $i++) { $result.Add($hostsLines[$i]) }
            $location = "inserted near existing group"
        } else {
            foreach ($hl in $hostsLines) { $result.Add($hl) }
            $result.Add('')
            if ($header) { $result.Add($header) }
            foreach ($ne in $newEntries) { $result.Add($ne) }
            $location = "appended as new block"
        }
    }

    $hostsLines = $result.ToArray()

    Write-Host
    Write-Host "  $groupName - Added $($newEntries.Count) entries ($location):" -ForegroundColor Green
    foreach ($e in $newEntries) {
        Write-Host "    + $e" -ForegroundColor Cyan
    }

    $totalSkipped += $skipped.Count
    $totalAdded += $newEntries.Count
}

# --- Write final result ---
if ($totalAdded -gt 0) {
    [System.IO.File]::WriteAllLines($hostsPath, $hostsLines)

    Write-Host
    Write-Host "  Flushing DNS cache..." -ForegroundColor DarkGray
    ipconfig /flushdns | Out-Null
    Write-Host "  DNS cache flushed." -ForegroundColor Green
}

Write-Host
Write-Host "  Done. $totalAdded added, $totalSkipped skipped." -ForegroundColor Green
Write-Host
pause
