import typer

from .config_cli import app as conf
from .db_cli import db_cli as db
from .doc_processor_cli import doc_processor_cli as docproc
from .file_processor_cli import file_processor_cli as proc
from .file_scanner_cli import file_scanner_cli as files

main_cli = typer.Typer(name="wembed", no_args_is_help=True)
main_cli.add_typer(conf, name="config", help="Configuration commands")
main_cli.add_typer(files, name="index", help="File scanning commands")
main_cli.add_typer(db, name="db", help="Database commands")
main_cli.add_typer(proc, name="proc", help="File processing commands")
main_cli.add_typer(docproc, name="doc", help="Document processing commands")


def main():
    main_cli()


if __name__ == "__main__":
    main()
