param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('p4-neutral', 'p4-causal_fact', 'p4-credit_rule', 'p5-visual', 'p5-necessity')]
    [string]$Task,
    [string]$Endpoint = 'root@connect.bjb2.seetacloud.com',
    [int]$Port = 36053
)

$ErrorActionPreference = 'Stop'
$hereDir = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$projectDir = (Resolve-Path -LiteralPath (Join-Path $hereDir '..\..\..')).Path
$pythonExe = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Project Python is missing' }
$remoteRun = '/root/autodl-tmp/monitor2/fresh_prerequisite_runs/20261007_dev_v2_01'
$kind, $name = $Task.Split('-', 2)
$remoteStage = "$remoteRun/extra/$kind/$name"
$localStage = Join-Path $hereDir "local_results\$kind\$name"
if (Test-Path -LiteralPath $localStage) { throw "Local stage already exists: $localStage" }
New-Item -ItemType Directory -Path $localStage | Out-Null

& scp -P $Port "${Endpoint}:$remoteStage/evidence.tar.gz" $localStage
if ($LASTEXITCODE -ne 0) { throw 'Evidence download failed' }
& scp -P $Port "${Endpoint}:$remoteStage/evidence.tar.gz.sha256" $localStage
if ($LASTEXITCODE -ne 0) { throw 'Checksum download failed' }
$archivePath = Join-Path $localStage 'evidence.tar.gz'
$checksumPath = Join-Path $localStage 'evidence.tar.gz.sha256'
$expectedSha = ((Get-Content -LiteralPath $checksumPath -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
$actualSha = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($expectedSha -ne $actualSha) { throw 'Downloaded evidence archive SHA mismatch' }
& tar -xzf $archivePath -C $localStage
if ($LASTEXITCODE -ne 0) { throw 'Evidence extraction failed' }

$env:PYTHONPATH = $hereDir
$rawDir = Join-Path $localStage 'raw'
$sealPath = Join-Path $localStage 'raw_seal.json'
if ($kind -eq 'p4') {
    foreach ($arm in @('access_gate', 'support_surface')) {
        $actualInput = Join-Path $localStage "inputs\$arm\model_input"
        $frozenInput = Join-Path $hereDir "p4_inputs\$name\$arm\model_input"
        foreach ($file in Get-ChildItem -LiteralPath $frozenInput -File) {
            $remoteCopy = Join-Path $actualInput $file.Name
            if (-not (Test-Path -LiteralPath $remoteCopy)) { throw "P4 input missing: $arm/$($file.Name)" }
            $frozenSha = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
            $remoteSha = (Get-FileHash -LiteralPath $remoteCopy -Algorithm SHA256).Hash
            if ($frozenSha -ne $remoteSha) { throw "P4 input changed: $arm/$($file.Name)" }
        }
    }
    & $pythonExe -m optional.p4_seal --raw-root $rawDir --seal $sealPath `
        --access-input (Join-Path $localStage 'inputs\access_gate\model_input') `
        --support-input (Join-Path $localStage 'inputs\support_surface\model_input') --verify
} else {
    $scenes = Join-Path $projectDir 'research\prerequisite_monitor\fresh_scenes_20261006'
    & $pythonExe -m optional.seal_p5 --raw-root $rawDir --seal $sealPath `
        --access-input (Join-Path $scenes 'access_gate\dev_v2\model_input') `
        --support-input (Join-Path $scenes 'support_surface\dev_v2\model_input') `
        --expected-count 18 --verify
}
if ($LASTEXITCODE -ne 0) { throw 'Local raw seal verification failed' }
$sealSha = (Get-FileHash -LiteralPath $sealPath -Algorithm SHA256).Hash.ToLowerInvariant()
$markerName = "${kind}_${name}_local_verified.sha256"
$markerPath = Join-Path $localStage $markerName
Set-Content -LiteralPath $markerPath -Value $sealSha -NoNewline -Encoding ascii
& scp -P $Port $markerPath "${Endpoint}:$remoteRun/$markerName"
if ($LASTEXITCODE -ne 0) { throw 'Could not upload local verification marker' }
Write-Output "Verified $Task; seal SHA-256: $sealSha"
