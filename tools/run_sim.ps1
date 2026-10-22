# Run QSPICE netlists/schematics headless and extract .meas results.
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\run_sim.ps1 [<sim>\x.qsch | <sim>\x.cir ...] -SimDir <project>\sim
#   <sim> = -SimDir, MANDATORY (no default; the tool serves every project), relative to the repo root or
#           absolute (paths below are relative to it). Missing or not an existing folder: exit 1 before
#           anything runs or is created.
#   default: every sim\*.qsch (netlisted first) plus every sim\*.cir without a same-named .qsch
#   -Analyze sim\analyze_x.py[,...]  run post-processing scripts after the simulations (before cleanup);
#                                    each script's output is kept as sim\out\<script>.summary.txt
#   -KeepRaw                         skip the Rule 6 cleanup (only when the engineer asks for raw data)
#   -Long                            also run LONG testbenches (Rule 8: a netlist line `* RUN_CLASS: LONG`,
#                                    estimated over 15 min). Without it they are skipped in the default batch,
#                                    and naming one fails (exit 1). Only after the engineer approves the run.
# QSPICE is stopped after 30 min (LONG: 4 h); a stopped run counts as a simulation error (exit 1).
# Outputs: <name>.qraw next to the netlist; sim\out\<name>.log (engine console),
#          sim\out\<name>.meas.txt (QPOST .meas results).
# Rule 6 cleanup (last step): deletes *.qraw / *.tmp under sim\ and *.csv under sim\out\ larger than 5 MB.
#   -CleanRaw (opt-in, default off; without it everything above is unchanged): instead of the size rule for .qraw, a run's
#             .qraw is deleted ONLY if the whole batch was clean (no failed / missing model / bloat / numerical-canary failure),
#             at least one -Analyze script ran and every analyzer exited 0, and -KeepRaw is not given; otherwise the raw files
#             stay and a line says why. *.tmp and big *.csv still follow the 5 MB rule. Use it with an -Analyze that writes
#             the small result files first, e.g. -Analyze C:\eda\tools\qraw_export.py (sim\out\<name>.csv).
#   -Analyze scripts get two environment variables: SIM_RAW_LIST (the .qraw paths of this batch, separated by ';') and
#             SIM_OUT_DIR (the sim\out folder).
# Exit codes: 0 ok | 1 simulation/QPOST/analysis error, or -SimDir missing / not a folder | 3 MISSING MODEL (Model Pre-loading Doctrine:
#             halt and ask the engineer to drop the verified model into sim\models\; never substitute one)
#             | 4 DATA RULE: a .tran netlist without a .save directive (Rule 6), not simulated
#             | 5 NUMERICAL ACCURACY: a canary_err_pct_* .meas exceeded 0.01 % (Rule 8); halt and report,
#               never relax tolerances and never roll back design files over it.
# -SimDir is checked by hand below, not with [Parameter(Mandatory)]: under `powershell -File` a missing
# mandatory parameter makes PowerShell prompt for it, which hangs a headless run instead of failing.
param([string[]]$Inputs, [string[]]$Analyze, [switch]$KeepRaw, [string]$SimDir, [switch]$Long, [switch]$CleanRaw)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$qux = 'C:\Program Files\QSPICE\QUX.exe'
$qspice = 'C:\Program Files\QSPICE\QSPICE64.exe'
$qpost = 'C:\Program Files\QSPICE\QPOST.exe'
# the hermetic sim tree lives inside the project root (Rule 2); -SimDir is relative to the repo root
if (-not $SimDir) {
    Write-Host "run_sim.ps1: -SimDir is required: the project's simulation folder, e.g. -SimDir <project>\sim" -ForegroundColor Red
    exit 1
}
$simRoot = if ([IO.Path]::IsPathRooted($SimDir)) { $SimDir } else { Join-Path $root $SimDir }
# checked before New-Item below, which would otherwise silently create a mistyped folder
if (-not (Test-Path -LiteralPath $simRoot -PathType Container)) {
    Write-Host "run_sim.ps1: -SimDir folder does not exist: $simRoot" -ForegroundColor Red
    exit 1
}
$out = Join-Path $simRoot 'out'
New-Item -ItemType Directory -Force $out | Out-Null

function Invoke-Headless($exe, $argList, $workDir, $log, $timeoutMs) {
    # Start-Process keeps native stderr out of PowerShell's error stream (no NativeCommandError noise)
    $p = Start-Process $exe -ArgumentList $argList -WorkingDirectory $workDir -NoNewWindow -PassThru `
        -RedirectStandardOutput "$log.stdout" -RedirectStandardError "$log.stderr"
    $null = $p.Handle   # PS 5.1 quirk: without touching Handle now, ExitCode is $null after exit
    if (-not $p.WaitForExit($timeoutMs)) { $p.Kill(); throw "$exe timed out after $timeoutMs ms" }
    # WriteAllLines always creates the file; `... | Set-Content` creates nothing when the tool printed nothing
    [IO.File]::WriteAllLines($log, [string[]]@(Get-Content "$log.stdout", "$log.stderr"))
    Remove-Item "$log.stdout", "$log.stderr"
    return $p.ExitCode
}

# Model pre-flight: every .include/.lib file must exist (relative paths resolve against the
# netlist's folder, exactly as QSPICE does), must be a SPICE model file by content (not a CAD
# symbol library), and every X instance's subckt must be defined in the netlist itself or in one
# of those files. Returns a list of human-readable problems.
function Test-Models($cir) {
    $dir = Split-Path $cir -Parent
    $problems = @(); $defined = @{}
    $files = @($cir); $seen = @{}
    while ($files.Count) {
        $f, $files = $files[0], @($files | Select-Object -Skip 1)
        if ($seen[$f]) { continue }; $seen[$f] = $true
        foreach ($line in Get-Content $f) {
            if ($line -match '^\s*\.(include|inc|lib)\s+"?([^"\s]+)"?') {
                $ref = $Matches[2]
                $path = if ([IO.Path]::IsPathRooted($ref)) { $ref } else { Join-Path $dir $ref }
                if (-not (Test-Path $path)) {
                    $problems += "model file not found: '$ref' (expected at $path) - referenced in $(Split-Path $f -Leaf)"
                    continue
                }
                # EXT-LIBRARY INTEGRITY: classify by content, never by extension (.lib is used by both
                # KiCad 5 symbol libraries and SPICE libraries)
                $full = (Resolve-Path $path).Path
                $head = (Get-Content $full -TotalCount 5 | Where-Object { $_.Trim() } | Select-Object -First 1)
                if ($head -match '^\s*(EESchema-LIBRARY|\(kicad_symbol_lib)') {
                    $problems += "'$ref' is a CAD SYMBOL library ($($Matches[1])), not a SPICE model - it can never be simulated"
                } elseif (-not (Select-String -Path $full -Pattern '^\s*\.(subckt|model)\s' -Quiet)) {
                    $problems += "'$ref' contains no .SUBCKT or .MODEL declaration - not a SPICE model file"
                } else { $files += $full }
            }
            if ($line -match '^\s*\.subckt\s+(\S+)') { $defined[$Matches[1].ToUpper()] = $true }
        }
    }
    foreach ($line in Get-Content $cir) {
        if ($line -match '^\s*X\S*\s+(.*)$') {
            $toks = @($Matches[1] -split '\s+' | Where-Object { $_ -and $_ -notmatch '=' })
            $sub = $toks[-1]
            if (-not $defined[$sub.ToUpper()]) { $problems += "subcircuit '$sub' is not defined in the netlist or any included model file (instance: $($line.Trim()))" }
        }
    }
    return $problems
}

$explicit = [bool]$Inputs   # testbenches named on the command line, not the default batch
if (-not $Inputs) {
    $qsch = @(Get-ChildItem $simRoot -Filter *.qsch -ErrorAction SilentlyContinue | ForEach-Object FullName)
    $cirs = @(Get-ChildItem $simRoot -Filter *.cir | Where-Object { -not (Test-Path ([IO.Path]::ChangeExtension($_.FullName, '.qsch'))) } | ForEach-Object FullName)
    $Inputs = $qsch + $cirs
}

$failed = $false; $missing = $false; $bloat = $false; $numfail = $false
$raws = @(); $analysisRan = $false   # -CleanRaw bookkeeping
foreach ($n in $Inputs) {
    $src = (Resolve-Path $n).Path
    $name = [IO.Path]::GetFileNameWithoutExtension($src)
    $dir = Split-Path $src -Parent
    $log = Join-Path $out "$name.log"
    $meas = Join-Path $out "$name.meas.txt"
    $cir = $src
    if ($src -like '*.qsch') {
        # QUX writes <name>.cir next to the schematic; that .cir is a build artifact, the .qsch is the source
        $null = Invoke-Headless $qux "-Netlist `"$src`"" $dir "$log.netlist" 60000
        Remove-Item "$log.netlist" -ErrorAction SilentlyContinue
        $cir = [IO.Path]::ChangeExtension($src, '.cir')
        if (-not (Test-Path $cir)) { Write-Host "[$name] NETLIST FAILED: QUX did not produce $cir"; $failed = $true; continue }
    }
    # Rule 8 LONG testbenches: out of the default batch, run only with -Long (engineer-approved).
    # $isLong, not $long: PowerShell variable names ignore case, so $long would be the -Long switch.
    $isLong = [bool](Select-String -LiteralPath $cir -Pattern '^\*\s*RUN_CLASS:\s*LONG\b' -Quiet)
    if ($isLong -and -not $Long) {
        if ($explicit) {
            Write-Host "[$name] HALT - LONG testbench (Rule 8): add -Long once the engineer has approved the run. Not simulated." -ForegroundColor Red
            $failed = $true
        } else {
            Write-Host "[$name] skipped: LONG testbench (Rule 8), not part of the default batch; run it with -Long once the engineer has approved the run"
        }
        continue
    }
    $problems = Test-Models $cir
    if ($problems) {
        Write-Host "[$name] HALT - MISSING MODEL (Model Pre-loading Doctrine). Not simulated." -ForegroundColor Red
        $problems | ForEach-Object { Write-Host "    - $_" }
        Write-Host "    Required action: the engineer must place the verified vendor .sub/.mod/.lib in $(Join-Path $dir 'models'), then re-run."
        $missing = $true; continue
    }
    # Rule 6: a transient run must restrict its capture with .save (an unconstrained 5 ms run here wrote 1.59 GB)
    $cirText = Get-Content $cir
    if (($cirText -match '^\s*\.tran\b') -and -not ($cirText -match '^\s*\.save\b')) {
        Write-Host "[$name] HALT - DATA RULE (Rule 6): .tran without .save. Add '.save <only the signals the .meas lines and analyzers read>'. Not simulated." -ForegroundColor Red
        $bloat = $true; continue
    }
    # stop a hung engine well past the 15 min hang threshold (LONG: 4 h); runtimes vary a lot (docs\lessons.md)
    $simTimeout = if ($isLong) { 4 * 3600000 } else { 30 * 60000 }
    try { $null = Invoke-Headless $qspice "`"$cir`"" $dir $log $simTimeout }
    catch { Write-Host "[$name] SIM FAILED: $($_.Exception.Message)" -ForegroundColor Red; $failed = $true; continue }
    if (Select-String -Path $log -Pattern 'Could not open file|Unknown subckt' -Quiet) {
        Write-Host "[$name] HALT - MISSING MODEL reported by QSPICE:" -ForegroundColor Red; Get-Content $log; $missing = $true; continue
    }
    if (Select-String -Path $log -Pattern 'Fatal error' -Quiet) { Write-Host "[$name] SIM FAILED"; Get-Content $log; $failed = $true; continue }
    $raws += [IO.Path]::ChangeExtension($cir, '.qraw')
    $null = Invoke-Headless $qpost "`"$cir`" -o `"$meas`"" $dir "$meas.qpost.log" 120000
    # a .meas on a signal that .save did not capture is only a QPOST *warning*; treat it as a failure
    # (QPOST writes these warnings into the -o results file, not to its console, so scan both)
    $qpWarn = @(Get-Content "$meas.qpost.log", $meas -ErrorAction SilentlyContinue | Where-Object { $_ -match 'Unknown (current|voltage|node)|Trouble parsing' })
    Remove-Item "$meas.qpost.log" -ErrorAction SilentlyContinue
    Write-Host "===== $name =====" ; Get-Content $meas
    if ($qpWarn) {
        Write-Host "[$name] QPOST FAILED - .meas references signals not captured by .save:" -ForegroundColor Red
        $qpWarn | ForEach-Object { Write-Host "    $_" }; $failed = $true
    }
    # Rule 8 numerical canary: every `.meas ... canary_err_pct_*` (deviation from an exact analytic
    # solution, in %) must be <= 0.01. Missing/NaN values count as failures.
    $measLines = @(Get-Content $meas)
    for ($i = 0; $i -lt $measLines.Count; $i++) {
        if ($measLines[$i] -match '^\.meas\s+\w+\s+(canary_err_pct\w*)\s') {
            $cname = $Matches[1]; $vals = @()
            for ($j = $i + 1; $j -lt $measLines.Count -and $measLines[$j] -notmatch '^\.meas'; $j++) {
                if ($measLines[$j] -match '([-+0-9.eE]+|nan)\s*$') { $vals += $Matches[1] }
            }
            foreach ($v in $vals) {
                $num = 0.0
                if (-not [double]::TryParse($v, [Globalization.NumberStyles]::Float, [Globalization.CultureInfo]::InvariantCulture, [ref]$num) -or $num -gt 0.01) {
                    Write-Host "[$name] NUMERICAL ACCURACY FAILURE (Rule 8): $cname = $v % (limit 0.01 %)" -ForegroundColor Red
                    $numfail = $true
                }
            }
        }
    }
}

if ($Analyze -and -not ($failed -or $missing -or $bloat -or $numfail)) {
    # `powershell -File` passes "-Analyze a,b" as one string, so split on commas
    $env:SIM_RAW_LIST = (@($raws | Select-Object -Unique) -join ';')
    $env:SIM_OUT_DIR = $out
    foreach ($script in @($Analyze | ForEach-Object { $_ -split ',' } | Where-Object { $_ })) {
        $sp = (Resolve-Path $script).Path
        $summary = Join-Path $out ([IO.Path]::GetFileNameWithoutExtension($sp) + '.summary.txt')
        $rc = Invoke-Headless 'python' "`"$sp`"" $root $summary 600000
        $analysisRan = $true
        Write-Host "===== analysis: $(Split-Path $sp -Leaf) -> $summary =====" ; Get-Content $summary
        if ($rc -ne 0) { Write-Host "[$(Split-Path $sp -Leaf)] ANALYSIS FAILED (exit $rc)" -ForegroundColor Red; $failed = $true }
    }
}

# Rule 6 automated cleanup: large intermediates go; logs, .meas results and summaries stay.
if (-not $KeepRaw) {
    $limit = 5MB
    $sizePattern = if ($CleanRaw) { @('*.tmp') } else { @('*.qraw', '*.tmp') }   # -CleanRaw: .qraw follows the rule below
    $big = @(Get-ChildItem $simRoot -Recurse -File -Include $sizePattern | Where-Object { $_.Length -gt $limit }) +
           @(Get-ChildItem $out -File -Filter *.csv | Where-Object { $_.Length -gt $limit })
    foreach ($f in $big) {
        Write-Host ("cleanup (Rule 6): deleting {0} ({1:N1} MB)" -f $f.FullName, ($f.Length / 1MB))
        Remove-Item -LiteralPath $f.FullName
    }
}
if ($CleanRaw) {
    # opt-in raw cleanup: only after a clean batch whose analyzers all exited 0 (see the header)
    $cleanBatch = -not ($failed -or $missing -or $bloat -or $numfail)
    if ($KeepRaw) {
        Write-Host "raw files kept (-KeepRaw)"
    } elseif (-not $cleanBatch) {
        Write-Host "raw files kept: the batch was not clean (see the failures above); fix and re-run"
    } elseif (-not $analysisRan) {
        Write-Host "raw files kept: no -Analyze script ran, so nothing has extracted the results yet"
    } else {
        foreach ($r in @($raws | Select-Object -Unique)) {
            if (Test-Path -LiteralPath $r) {
                Write-Host ("cleanup (-CleanRaw): deleting {0} ({1:N1} MB) after the analyzers exited 0" -f $r, ((Get-Item -LiteralPath $r).Length / 1MB))
                Remove-Item -LiteralPath $r
            }
        }
    }
}
if ($missing) { exit 3 }
if ($bloat) { exit 4 }
if ($numfail) { exit 5 }
if ($failed) { exit 1 }
