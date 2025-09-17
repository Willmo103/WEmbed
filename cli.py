from config import config_cli as conf
from file_scanner import file_filter_cli as files
from db import db_cli as db
import typer

main_cli = typer.Typer(name="jstr", no_args_is_help=True)

main_cli.add_typer(conf, name="config", help="Configuration commands")
main_cli.add_typer(files, name="index", help="File scanning commands")
main_cli.add_typer(db, name="db", help="Database commands")

if __name__ == "__main__":
    main_cli()
