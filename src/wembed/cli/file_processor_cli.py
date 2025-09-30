from typer import Typer, echo

from wembed.db import FileRecordRepo, InputRecordRepo, RepoRecordRepo, VaultRecordRepo
from wembed.file_processor import process_repo_files, process_vault_files

from . import cli_db_service

file_processor_cli = Typer(
    name="process", no_args_is_help=True, help="File Processing Commands"
)


@file_processor_cli.command(
    name="vaults", help="Process all vault files into FileRecords"
)
def process_vaults_command():
    """Process all scanned vault files."""
    echo("Starting vault file processing...")
    process_vault_files(cli_db_service)


@file_processor_cli.command(
    name="repos", help="Process all repo files into FileRecords"
)
def process_repos_command():
    """Process all scanned repository files."""
    echo("Starting repository file processing...")
    process_repo_files(cli_db_service)


@file_processor_cli.command(name="all", help="Process all files (vaults and repos)")
def process_all_command():
    """Process all scanned files."""
    echo("Starting processing of all files...")
    process_vault_files(cli_db_service)
    process_repo_files(cli_db_service)
    echo("All file processing complete!")


@file_processor_cli.command(name="status", help="Show processing status")
def show_status_command():
    """Show the current processing status."""
    session = cli_db_service.get_session()
    try:
        # Count records
        vault_count = len(VaultRecordRepo.get_all(session))
        repo_count = len(RepoRecordRepo.get_all(session))
        file_count = len(FileRecordRepo.get_all(session))
        pending_inputs = len(InputRecordRepo.get_by_status(session, "pending"))

        echo("Processing Status:")
        echo(f"  Vaults discovered: {vault_count}")
        echo(f"  Repositories discovered: {repo_count}")
        echo(f"  Files processed: {file_count}")
        echo(f"  Pending document processing: {pending_inputs}")

    finally:
        session.close()


if __name__ == "__main__":
    file_processor_cli()
