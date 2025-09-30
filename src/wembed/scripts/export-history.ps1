<#
.SYNOPSIS
    Export the currently powershell session command history as a JSON file.

.DESCRIPTION
    This script exports the command history of the current PowerShell session to a JSON file.
    The file will be saved to the path provided as an argument when running the script.

    Output Schema:
        [
            {
                "id": uuid (STRING) from python uuid.uuid4(),
                "command": STRING,
                "start_time": DATETIME,
                "end_time": DATETIME,
                "duration_seconds": FLOAT,
                "host": STRING,
                "user": STRING,
            },
            ...
        ]
    Output File Name Format: <OutDir>\powershell_history_YYYYMMDD_HHMM_export.json
    Note: The script currently names the file: "$timestamp-history.json" in the code.

.PARAMETER OutDir
    The directory where the command history JSON file will be saved.
    If the directory does not exist, it will be created.

.PARAMETER Count
    Specifies the maximum number of history entries to retrieve.
    If omitted, all history entries in the current session are exported.

.OUTPUTS
    System.String. The full path to the exported JSON file.

.EXAMPLE
    .\export-history.ps1 -OutDir ".\exports"
    Exports all command history to a file like ".\exports\20250928_1637-history.json".

.EXAMPLE
    .\export-history.ps1 -OutDir ".\history_dumps" -Count 50
    Exports the last 50 command history items to a file in the ".\history_dumps" directory.

.NOTES
    Author: Will Morris
    Date: 2025-09-28
    Version: 1.0
    License: MIT License
    GitHub: https://github.com/Willmo103/WEmbed/blob/main/src/wembed/scripts/export-history.ps1
#>
[CmdletBinding(
    SupportsShouldProcess = $true,
    ConfirmImpact = 'Low'
)]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$OutDir,

    [Parameter(Mandatory = $false)]
    [int]$Count = 0
)

function Export-HistoryToJSON {
    <#
.SYNOPSIS
    Exports the current PowerShell session command history to a JSON file.
.DESCRIPTION
    Handles the main logic of getting, processing, and exporting history items.
#>
    # Use fully qualified cmdlet names and avoid aliases as requested
    if (-not (Test-Path -Path $OutDir)) {
        # Create directory if it doesn't exist
        Write-Verbose "Creating output directory: $OutDir"
        New-Item -Path $OutDir -ItemType Directory -Force | Out-Null
    }

    # Generate a cache file name
    $timestamp = Get-Date -Format "yyyyMMdd_HHmm"
    # Using the name defined in the script logic, not the example
    $fileName = "$timestamp-history.json"
    $json_cache = Join-Path -Path $OutDir -ChildPath $fileName

    # Get history with limit if specified
    $history = if ($Count -gt 0) {
        Write-Verbose "Exporting last $Count history entries."
        Get-History -Count $Count
    }
    else {
        Write-Verbose "Exporting all history entries from the current session."
        Get-History
    }

    if ($history.Count -eq 0) {
        Write-Host "No history items to export" -ForegroundColor Yellow
        return
    }

    Write-Verbose "Processing $($history.Count) history items..."

    # Process each history item
    $processedHistory = $history | ForEach-Object {
        # Get environment variables for host and user
        $hostName = $env:COMPUTERNAME
        $userName = $env:USERNAME

        # Calculate duration
        $duration = if ($_.EndExecutionTime -and $_.StartExecutionTime) {
            ($_.EndExecutionTime - $_.StartExecutionTime).TotalSeconds
        }
        else {
            $null
        }

        # Create history object
        [PSCustomObject]@{
            # Note: This requires 'python' to be in the PATH to generate a UUID.
            id               = (python -c "import uuid; print(uuid.uuid4())").Trim()
            command          = $_.CommandLine
            start_time       = $_.StartExecutionTime
            end_time         = $_.EndExecutionTime
            duration_seconds = $duration
            host             = $hostName
            user             = $userName
        }
    }

    # Convert to JSON
    $jsonContent = $processedHistory | ConvertTo-Json -Depth 3

    # Save to cache file
    Write-Verbose "Saving history to $json_cache"
    Set-Content -Path $json_cache -Value $jsonContent -Encoding UTF8

    # Output the path to the exported file
    Write-Host $json_cache -ForegroundColor Green
    return $json_cache # Return the path as specified in .OUTPUTS
}

Export-HistoryToJSON
