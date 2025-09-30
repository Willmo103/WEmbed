# wembed/cli.py

import json

import typer
from typing_extensions import Annotated

from wembed import PROD_CONFIG_DIR

# It's crucial to import the config class AFTER typer,
# so CLI --help generation doesn't fail if a config dir is missing.
from wembed.config import CONFIG_DIR
from wembed.config.model import AppConfig
from wembed.constants import HEADERS, IGNORE_EXTENSIONS, IGNORE_PARTS, MD_XREF

app = typer.Typer(no_args_is_help=True, help="Wembed Configuration and Management CLI")


@app.command()
def show():
    """
    Load and display the current application configuration as JSON.
    """
    try:
        config = AppConfig()
        # Manually add non-field properties for a complete view
        full_config_dict = config.model_dump()
        full_config_dict["md_vault_path"] = str(config.md_vault_path)
        full_config_dict["active_config_dir"] = str(CONFIG_DIR)

        print(json.dumps(full_config_dict, indent=2, default=str))

    except Exception as e:
        typer.secho(f"Error loading configuration: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def init(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing configuration files with defaults.",
        ),
    ] = False,
):
    """
    Initialize the production config directory (~/.wembed) with default files.
    """
    if CONFIG_DIR != PROD_CONFIG_DIR:
        typer.secho(
            "Initialization is only available for production mode.",
            fg=typer.colors.YELLOW,
        )
        typer.secho(
            f"Currently in dev mode, using config directory: {CONFIG_DIR}",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit()

    typer.echo(f"Initializing config directory at: {PROD_CONFIG_DIR}")

    default_config = AppConfig()
    config_files = {
        "appconfig.json": default_config.model_dump(
            exclude={"headers", "ignore_extensions", "ignore_parts", "md_xref"}
        ),
        "headers.json": HEADERS,
        "ignore_exts.json": IGNORE_EXTENSIONS,
        "ignore_parts.json": IGNORE_PARTS,
        "md_xref.json": MD_XREF,
    }

    for filename, content in config_files.items():
        file_path = PROD_CONFIG_DIR / filename
        if not file_path.exists() or force:
            with open(file_path, "w") as f:
                json.dump(content, f, indent=2, default=str)
            typer.secho(f"Created default file: {file_path}", fg=typer.colors.GREEN)
        else:
            typer.secho(f"Skipping existing file: {file_path}", fg=typer.colors.CYAN)

    # Ensure markdown vault exists
    (PROD_CONFIG_DIR / "md_vault").mkdir(exist_ok=True)
    typer.secho("Initialization complete.", fg=typer.colors.BRIGHT_GREEN)


if __name__ == "__main__":
    app()
