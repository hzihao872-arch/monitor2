param(
    [string]$Endpoint = 'root@connect.bjb2.seetacloud.com',
    [int]$Port = 36053
)

$ErrorActionPreference = 'Stop'
$hereDir = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$projectDir = (Resolve-Path -LiteralPath (Join-Path $hereDir '..\..\..')).Path
$pythonExe = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw 'Project Python is missing' }
$remoteRun = '/root/autodl-tmp/monitor2/fresh_prerequisite_runs/20261007_dev_v2_01'
$remoteStage = "$remoteRun/extra/p6/direct"
$localStage = Join-Path $hereDir 'local_results\p6\direct'
if (Test-Path -LiteralPath $localStage) { throw "Local stage already exists: $localStage" }
New-Item -ItemType Directory -Path $localStage | Out-Null

& scp -P $Port "${Endpoint}:$remoteStage/evidence.tar.gz" $localStage
if ($LASTEXITCODE -ne 0) { throw 'P6 evidence download failed; local directory preserved' }
& scp -P $Port "${Endpoint}:$remoteStage/evidence.tar.gz.sha256" $localStage
if ($LASTEXITCODE -ne 0) { throw 'P6 checksum download failed; local directory preserved' }
$archive = Join-Path $localStage 'evidence.tar.gz'
$checksum = Join-Path $localStage 'evidence.tar.gz.sha256'
$expectedSha = ((Get-Content -LiteralPath $checksum -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
$actualSha = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
if ($expectedSha -ne $actualSha) { throw 'P6 archive SHA mismatch' }
& tar -xzf $archive -C $localStage
if ($LASTEXITCODE -ne 0) { throw 'P6 archive extraction failed' }

$codeManifest = Get-Content -LiteralPath (Join-Path $hereDir 'p6_model_code_manifest.json') -Raw | ConvertFrom-Json
foreach ($item in $codeManifest.files.PSObject.Properties) {
    $downloaded = Join-Path $localStage ('code\' + $item.Name.Replace('/', '\'))
    if (-not (Test-Path -LiteralPath $downloaded)) { throw "P6 code missing: $($item.Name)" }
    $sha = (Get-FileHash -LiteralPath $downloaded -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($sha -ne $item.Value) { throw "P6 code SHA mismatch: $($item.Name)" }
}

$sealPath = Join-Path $localStage 'raw_seal.json'
if (-not (Test-Path -LiteralPath $sealPath)) {
    Write-Output "P6 partial evidence downloaded and archive verified at $localStage; no full raw seal"
    return
}
$scenes = Join-Path $projectDir 'research\prerequisite_monitor\fresh_scenes_20261006'
$env:PYTHONPATH = $hereDir
& $pythonExe -m p6pkg.seal --raw-root (Join-Path $localStage 'raw') --seal $sealPath `
    --access-input (Join-Path $scenes 'access_gate\dev_v2\model_input') `
    --support-input (Join-Path $scenes 'support_surface\dev_v2\model_input') `
    --expected-count 18 --verify
if ($LASTEXITCODE -ne 0) { throw 'P6 local raw seal verification failed' }
$sealSha = (Get-FileHash -LiteralPath $sealPath -Algorithm SHA256).Hash.ToLowerInvariant()
$marker = Join-Path $localStage 'p6_direct_local_verified.sha256'
Set-Content -LiteralPath $marker -Value $sealSha -NoNewline -Encoding ascii
& scp -P $Port $marker "${Endpoint}:$remoteRun/p6_direct_local_verified.sha256"
if ($LASTEXITCODE -ne 0) { throw 'Could not upload P6 local verification marker' }
Write-Output "Verified P6 direct; seal SHA-256: $sealSha"
