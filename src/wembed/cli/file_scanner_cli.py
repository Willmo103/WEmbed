import typer

from wembed.file_scanner import (
    convert_scan_results_to_records,
    scan_list,
    scan_repos,
    scan_vaults,
    store_scan_results,
)

from . import cli_db_service

file_scanner_cli = typer.Typer(
    name="scan", no_args_is_help=True, help="File Scanning Commands"
)


@file_scanner_cli.command(name="repos", help="Scan for git repos", no_args_is_help=True)
def scan_repos_command(
    path: str = typer.Argument(..., help="Path to scan", dir_okay=True, file_okay=False)
):
    """Scan for repositories and store the results."""
    results = scan_repos(path)
    if results:
        store_scan_results(results)
        convert_scan_results_to_records(results, db_svc=cli_db_service)
        typer.echo(f"Found and processed {len(results)} repos.")
    else:
        typer.secho("No repositories found.", fg=typer.colors.YELLOW)


@file_scanner_cli.command(
    name="vaults", help="Scan for Obsidian vaults", no_args_is_help=True
)
def scan_vaults_command(
    path: str = typer.Argument(..., help="Path to scan", dir_okay=True, file_okay=False)
):
    """Scan for Obsidian vaults and store the results."""
    results = scan_vaults(path)
    if results:
        store_scan_results(results)
        convert_scan_results_to_records(results, db_svc=cli_db_service)
        typer.echo(f"Found and processed {len(results)} vaults.")
    else:
        typer.secho("No vaults found.", fg=typer.colors.YELLOW)


@file_scanner_cli.command(
    name="list", help="List all files in a directory", no_args_is_help=True
)
def list_files_command(
    path: str = typer.Argument(
        ..., help="Path to list files", dir_okay=True, file_okay=False
    ),
    json: bool = typer.Option(False, "--json", "-j", help="Output as JSON."),
    nl: bool = typer.Option(
        False, "--nl", "-n", help="Output as newline-delimited list."
    ),
):
    """List files in a directory and optionally store results."""
    results = scan_list(path)
    if not results:
        typer.secho("No files found.", fg=typer.colors.YELLOW)
        return

    # Store results
    store_scan_results(results, db_svc=cli_db_service)

    # Format output
    result = results[0]  # LIST scan returns only one result
    if json:
        typer.echo(result.model_dump_json(indent=2))
    elif nl:
        typer.echo("\n".join(result.files))
    else:
        # Default output is also newline-delimited
        typer.echo("\n".join(result.files))


if __name__ == "__main__":
    file_scanner_cli()
