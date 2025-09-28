import typer
from rich.console import Console
from typing_extensions import Annotated

from . import cli_db_service

# Create a Typer app for the 'db' subcommand
db_cli = typer.Typer(
    name="db",
    no_args_is_help=True,
    help="Commands for managing the application database.",
)

# Using rich for better console output
console = Console()


@db_cli.command(name="test")
def test_db_connection():
    """Tests the connection to the PostgreSQL database specified in the config."""
    console.print("Attempting to connect to the database...")
    try:
        if cli_db_service.test_connection():
            console.print("[bold green]✔ Database connection successful.[/bold green]")
        else:
            console.print(
                "[bold red]❌ Database connection failed. Check your URI and ensure the database is running.[/bold red]"
            )
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]❌ An unexpected error occurred: {e}[/bold red]")
        raise typer.Exit(code=1)


@db_cli.command(name="init")
def init_database(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force drop all existing tables before re-initializing. THIS WILL DELETE ALL DATA.",
        ),
    ] = False,
):
    """Initializes the database by creating all necessary tables."""
    if force:
        console.print(
            "[bold yellow]WARNING: The --force flag will delete all existing data.[/bold yellow]"
        )
        if not typer.confirm("Are you sure you want to proceed?"):
            raise typer.Abort()

    console.print("Initializing database tables...")
    try:
        success, msg = cli_db_service.initialize_tables(force=force)

        if success:
            console.print(f"[bold green]✔ {msg}[/bold green]")
        else:
            console.print(f"[bold red]❌ {msg}[/bold red]")
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]❌ An unexpected error occurred: {e}[/bold red]")
        raise typer.Exit(code=1)
