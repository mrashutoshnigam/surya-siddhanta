<#
.SYNOPSIS
    Build the single-image Surya Siddhanta UI and publish it to Docker Hub.

.DESCRIPTION
    Builds Dockerfile.ui -- the image that serves the React UI on :80/:443 with
    the FastAPI backend held on loopback inside the container -- tags the result
    as both :latest and :<Version>, and pushes both tags to Docker Hub.

    Both tags point at one build, so :latest and the version tag always share a
    digest. The script stops at the first failing docker command rather than
    pushing a half-built image.

.PARAMETER Version
    The version tag to publish alongside :latest. Defaults to 0.1.

.PARAMETER Repository
    The Docker Hub repository, as <user>/<name>. Defaults to the project's own.

.PARAMETER SkipPush
    Build and tag only. Use to verify a build without touching the registry.

.PARAMETER NoCache
    Build without the layer cache. Slow; use when a base image has moved or a
    cached layer is suspect.

.EXAMPLE
    ./docker/publish.ps1
    Builds and pushes mrashutoshnigam/surya-siddhanta:latest and :0.1.

.EXAMPLE
    ./docker/publish.ps1 -Version 0.2 -SkipPush
    Builds and tags 0.2 locally, pushes nothing.
#>
[CmdletBinding()]
param(
    [Parameter()]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]{0,126}$')]
    [string]$Version = '0.1',

    [Parameter()]
    [ValidatePattern('^[a-z0-9]+(?:[._-][a-z0-9]+)*/[a-z0-9]+(?:[._-][a-z0-9]+)*$')]
    [string]$Repository = 'mrashutoshnigam/surya-siddhanta',

    [switch]$SkipPush,
    [switch]$NoCache
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Docker {
    <#
    .SYNOPSIS
        Run docker with the given arguments and throw on a non-zero exit code.
    .DESCRIPTION
        PowerShell does not treat a native command's exit status as an error, so
        every docker call is checked explicitly -- otherwise a failed build would
        fall through to the push and publish whatever was tagged last.
    .PARAMETER Arguments
        The argument list passed to the docker executable.
    #>
    param([Parameter(Mandatory)][string[]]$Arguments)

    Write-Host "> docker $($Arguments -join ' ')" -ForegroundColor DarkCyan
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "docker $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Get-DockerHubUser {
    <#
    .SYNOPSIS
        The Docker Hub account the local docker client is logged in as, or $null.
    .DESCRIPTION
        Checked up front so a missing or wrong login is reported in a second
        rather than several minutes into a build. Docker Desktop keeps the
        secret in a credential helper rather than config.json, so the helper is
        queried when config.json names one; a plain config.json auths entry is
        read directly for installs that store credentials there.
    #>
    $configPath = Join-Path $env:USERPROFILE '.docker/config.json'
    if (-not (Test-Path $configPath)) { return $null }
    try { $config = Get-Content $configPath -Raw | ConvertFrom-Json } catch { return $null }

    $hubKey = 'https://index.docker.io/v1/'
    $names  = $config.PSObject.Properties.Name

    if ($names -contains 'credsStore' -and $config.credsStore) {
        try {
            $listed = '' | & "docker-credential-$($config.credsStore)" list 2>$null | ConvertFrom-Json
            if ($listed -and ($listed.PSObject.Properties.Name -contains $hubKey)) {
                return $listed.$hubKey
            }
        } catch {
            # Helper missing or uncooperative: fall through to config.json.
        }
    }

    if ($names -contains 'auths' -and ($config.auths.PSObject.Properties.Name -contains $hubKey)) {
        $entry = $config.auths.$hubKey
        if ($entry.PSObject.Properties.Name -contains 'auth' -and $entry.auth) {
            $decoded = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($entry.auth))
            return $decoded.Split(':')[0]
        }
        return '<unknown>'
    }

    return $null
}


$repoRoot   = Split-Path -Parent $PSScriptRoot
$dockerfile = Join-Path $repoRoot 'Dockerfile.ui'
if (-not (Test-Path $dockerfile)) {
    throw "Dockerfile.ui not found at $dockerfile"
}

$latestTag  = "${Repository}:latest"
$versionTag = "${Repository}:${Version}"

if (-not $SkipPush) {
    $hubUser = Get-DockerHubUser
    if (-not $hubUser) {
        throw "Not logged in to Docker Hub. Run 'docker login' first, or pass -SkipPush to build only."
    }
    # A push to someone else's namespace fails with a 403 only after the layers
    # have uploaded, so the mismatch is worth catching here.
    $namespace = $Repository.Split('/')[0]
    if ($hubUser -ne '<unknown>' -and $hubUser -ne $namespace) {
        throw "Logged in to Docker Hub as '$hubUser' but $Repository is under '$namespace'. Run 'docker login' as $namespace."
    }
    Write-Host "Docker Hub login: $hubUser" -ForegroundColor DarkGray
}

Write-Host "Building $versionTag and $latestTag from Dockerfile.ui" -ForegroundColor Cyan

$buildArgs = @('build', '-f', $dockerfile, '-t', $latestTag, '-t', $versionTag)
if ($NoCache) { $buildArgs += '--no-cache' }
$buildArgs += $repoRoot
Invoke-Docker $buildArgs

if ($SkipPush) {
    Write-Host "Built and tagged; push skipped." -ForegroundColor Yellow
    Invoke-Docker @('image', 'inspect', $versionTag, '--format', '{{.Id}} {{join .RepoTags ", "}}')
    return
}

# Pushed separately rather than with --all-tags: the repository may carry older
# tags that this build has nothing to do with.
Invoke-Docker @('push', $versionTag)
Invoke-Docker @('push', $latestTag)

Write-Host "Published $versionTag and $latestTag" -ForegroundColor Green
Write-Host "  docker run -p 80:80 -p 443:443 -e DEEPSEEK_API_KEY=... $versionTag" -ForegroundColor DarkGray
