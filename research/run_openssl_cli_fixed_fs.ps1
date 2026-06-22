param(
    [ValidateSet("sha256", "aesctr", "hmac")]
    [string]$Mode = "sha256",

    [string]$Tag = "",
    [int]$InputBytes = 65536,
    [int]$Seed = 0,
    [string]$InputPath = "/tmp/openssl_cli_input.bin",
    [string]$OutputPath = "/tmp/openssl_cli_aesctr_output.bin",
    [string]$KeyHex = "00112233445566778899aabbccddeeff",
    [string]$IvHex = "0102030405060708090a0b0c0d0e0f10",
    [string]$HmacKey = "COPPER-fixed-HMAC-key",

    [string[]]$Policies = @("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack"),

    [string]$Gem5 = "external/gem5/build/ARM/gem5.fast.exe",
    [string]$OpenSslBinary = "research/bin/aarch64_ubuntu_openssl_cli",
    [string]$MsysRoot = "tools/msys64",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$msysRootPath = Join-Path $repoRoot $MsysRoot
if (Test-Path $msysRootPath) {
    $runtimePaths = @(
        (Join-Path $msysRootPath "ucrt64/bin"),
        (Join-Path $msysRootPath "usr/bin")
    ) | Where-Object { Test-Path $_ }
    if ($runtimePaths.Count -gt 0) {
        $env:PATH = ($runtimePaths -join [IO.Path]::PathSeparator) + [IO.Path]::PathSeparator + $env:PATH
    }
}

$validPolicies = @("none", "naive", "copper_clpd64k_peb", "spp", "spp_copper_slack")
$Policies = @($Policies | ForEach-Object { $_ -split "," } | Where-Object { $_ -ne "" })
foreach ($policy in $Policies) {
    if ($validPolicies -notcontains $policy) {
        throw "Unknown policy '$policy'. Valid policies: $($validPolicies -join ', ')"
    }
}

if ($Tag -eq "") {
    $Tag = switch ($Mode) {
        "sha256" { "fixed_64k" }
        "aesctr" { "aesctr_64k" }
        "hmac" { "hmac_64k" }
    }
}

$common = @(
    "research/gem5_arm_ubuntu_fs_copper_workload.py",
    "--kernel-arg", "no_systemd=true",
    "--switch-roi-to-timing",
    "--candidate-min", "0x400000",
    "--candidate-max", "0x0000ffffffffffff",
    "--pointer-bytes", "8",
    "--pointer-alignment", "8",
    "--recent-entries", "4096",
    "--value-token-bits", "48",
    "--prefetch-queue-size", "64",
    "--native-only",
    "--native-binary", $OpenSslBinary,
    "--native-preload-pointer-file",
    "--native-preload-path", $InputPath,
    "--native-preload-bytes", "$InputBytes",
    "--native-preload-seed", "$Seed"
)

$modeArgs = switch ($Mode) {
    "sha256" {
        @(
            "--native-arg=dgst",
            "--native-arg=-sha256",
            "--native-arg=$InputPath"
        )
    }
    "aesctr" {
        @(
            "--native-arg=enc",
            "--native-arg=-aes-128-ctr",
            "--native-arg=-K",
            "--native-arg=$KeyHex",
            "--native-arg=-iv",
            "--native-arg=$IvHex",
            "--native-arg=-in",
            "--native-arg=$InputPath",
            "--native-arg=-out",
            "--native-arg=$OutputPath",
            "--native-after-arg=dgst",
            "--native-after-arg=-sha256",
            "--native-after-arg=$OutputPath"
        )
    }
    "hmac" {
        @(
            "--native-arg=dgst",
            "--native-arg=-sha256",
            "--native-arg=-hmac",
            "--native-arg=$HmacKey",
            "--native-arg=$InputPath"
        )
    }
}

function Get-PolicyArgs {
    param([string]$Policy)

    switch ($Policy) {
        "none" {
            return @("--prefetcher", "none")
        }
        "naive" {
            return @("--prefetcher", "naive", "--provenance-entries", "65536")
        }
        "copper_clpd64k_peb" {
            return @(
                "--prefetcher", "copper",
                "--provenance-entries", "65536",
                "--line-provenance",
                "--clear-copper-on-stats-reset"
            )
        }
        "spp" {
            return @("--prefetcher", "spp", "--provenance-entries", "65536")
        }
        "spp_copper_slack" {
            return @(
                "--prefetcher", "spp_copper_slack",
                "--provenance-entries", "65536",
                "--line-provenance",
                "--clear-copper-on-stats-reset"
            )
        }
    }
}

$prefix = switch ($Mode) {
    "sha256" { "COPPER_OPENSSL_CLI_FIXED" }
    "aesctr" { "COPPER_OPENSSL_CLI_AESCTR" }
    "hmac" { "COPPER_OPENSSL_CLI_HMAC" }
}

foreach ($policy in $Policies) {
    $outdir = "research/results/gem5_arm_ubuntu_fs_osslcli_${Tag}_${policy}"
    $stdout = "${outdir}.host.out"
    $stderr = "${outdir}.host.err"
    $args = @("--outdir=$outdir") + $common + $modeArgs + (Get-PolicyArgs $policy)

    Write-Host "${prefix}_START $policy"
    if ($DryRun) {
        Write-Host "$Gem5 $($args -join ' ')"
        continue
    }

    $process = Start-Process `
        -FilePath $Gem5 `
        -ArgumentList $args `
        -NoNewWindow `
        -Wait `
        -PassThru `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr
    $exitCode = $process.ExitCode
    if ($exitCode -ne 0) {
        throw "gem5 failed for mode=$Mode tag=$Tag policy=$policy with exit code $exitCode. See $stdout and $stderr."
    }
    Write-Host "${prefix}_DONE $policy"
}
