from config import config_cli as conf
from file_scanner import file_filter_cli as files
import typer

main_cli = typer.Typer(name="jstr", no_args_is_help=True)

main_cli.add_typer(conf, name="config", help="Configuration commands")
main_cli.add_typer(files, name="files", help="File scanning commands")


if __name__ == "__main__":
    main_cli()
