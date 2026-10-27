$ErrorActionPreference = "SilentlyContinue"

function Write-Result {
    param(
        [string]$Level,
        [string]$Message
    )

    $prefix = switch ($Level) {
        "OK" { "[OK]  " }
        "WARN" { "[WARN]" }
        "FAIL" { "[FAIL]" }
        default { "[INFO]" }
    }

    Write-Host "$prefix $Message"
}

function Check-Command {
    param(
        [string]$Name
    )

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        Write-Result "OK" "$Name found at $($cmd.Source)"
    } else {
        Write-Result "FAIL" "$Name not found in PATH"
    }
}

function Get-NpcapEntry {
    $paths = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )

    foreach ($path in $paths) {
        $entry = Get-ItemProperty $path | Where-Object { $_.DisplayName -like "*Npcap*" } | Select-Object -First 1
        if ($null -ne $entry) {
            return $entry
        }
    }

    return $null
}

Write-Host "=== Net-Lab Windows Environment Check ==="

Check-Command "cmake"
Check-Command "gcc"
Check-Command "gdb"

$npcap = Get-NpcapEntry
if ($null -eq $npcap) {
    Write-Result "FAIL" "Npcap is not installed"
} else {
    $version = $npcap.DisplayVersion
    Write-Result "OK" "Npcap version detected: $version"

    try {
        $detected = [Version]$version
        $recommended = [Version]"1.31"
        if ($detected -eq $recommended) {
            Write-Result "OK" "Npcap matches the recommended version 1.31"
        } elseif ($detected -gt $recommended) {
            Write-Result "WARN" "Npcap is newer than 1.31; downgrade if udp_server/tcp_server behaves abnormally"
        } else {
            Write-Result "WARN" "Npcap is older than 1.31; upgrade to 1.31 if capture/send is unstable"
        }
    } catch {
        Write-Result "WARN" "Could not compare Npcap version automatically"
    }
}

$npcapConfig = Get-ItemProperty "HKLM:\SOFTWARE\Npcap" -ErrorAction SilentlyContinue
if ($null -ne $npcapConfig) {
    if ($npcapConfig.PSObject.Properties.Name -contains "WinPcapCompatible") {
        if ($npcapConfig.WinPcapCompatible -eq 1) {
            Write-Result "OK" "WinPcap-compatible mode appears to be enabled"
        } else {
            Write-Result "WARN" "WinPcap-compatible mode appears to be disabled; reinstall Npcap with compatibility mode"
        }
    } else {
        Write-Result "WARN" "Could not verify WinPcap-compatible mode automatically; confirm it manually during installation"
    }
}

$adapters = Get-NetAdapter -Physical -ErrorAction SilentlyContinue
if ($null -ne $adapters -and $adapters.Count -gt 0) {
    Write-Result "OK" "Detected physical adapters:"
    $adapters | ForEach-Object {
        Write-Host ("       {0} ({1}) - {2}" -f $_.Name, $_.InterfaceDescription, $_.Status)
    }

    $wired = $adapters | Where-Object { $_.NdisPhysicalMedium -notmatch "Wireless" }
    if ($null -eq $wired -or $wired.Count -eq 0) {
        Write-Result "WARN" "No wired adapter detected; if checksum offload options are missing, consider the Linux/WSL veth workflow"
    }
} else {
    Write-Result "WARN" "Could not enumerate network adapters automatically"
}

Write-Host ""
Write-Host "Manual checks still required:"
Write-Host "  1. Open the net-lab root directory directly in VSCode."
Write-Host "  2. Select the MinGW / GCC CMake kit."
Write-Host "  3. Confirm NET_IF_IP is on the same subnet as your test adapter, but uses a different host number."
Write-Host "  4. In Wireshark, enable IPv4 / UDP / TCP checksum validation."
