import typer

from wembed.config import AppConfig
from wembed.db.input_record import InputRecordRepo

from ..db import ChunkRecordRepo, DBService, DocumentRecordRepo
from ..dl_doc_processor import DlDocProcessor
from . import cli_db_service

doc_processor_cli = typer.Typer(
    name="doc-processor",
    help="Document processing commands",
    no_args_is_help=True,
)


# CLI Interface
@doc_processor_cli.command(name="convert", help="Convert a single source (URL or file)")
def convert_source_command(
    source: str = typer.Argument(..., help="Source URL or file path to convert"),
) -> None:
    """Convert a single source to a DoclingDocument."""
    processor = DlDocProcessor()
    result = processor.convert_source(source, db_svc=cli_db_service)

    if result:
        typer.echo(f"Successfully processed source. Document ID: {result}")
    else:
        typer.secho("Failed to process source", fg=typer.colors.RED)


@doc_processor_cli.command(
    name="process-pending", help="Process all pending input records"
)
def process_pending_command():
    """Process all pending input records in the database."""
    processor = DlDocProcessor()
    processor.process_pending_inputs(db_svc=cli_db_service)


@doc_processor_cli.command(name="process-file", help="Process a specific file record")
def process_file_command(
    file_id: str = typer.Argument(..., help="File record ID to process"),
):
    """Process a specific file record by ID."""
    processor = DlDocProcessor()
    result = processor.process_file_record(file_id, db_svc=cli_db_service)

    if result:
        typer.echo(f"Successfully processed file. Document ID: {result}")
    else:
        typer.secho("Failed to process file", fg=typer.colors.RED)


@doc_processor_cli.command(name="status", help="Show document processing status")
def show_status_command():
    """Show the current document processing status."""
    session = cli_db_service.get_session()
    try:
        pending_count = len(InputRecordRepo.get_unprocessed(session))
        processed_count = len(InputRecordRepo.get_by_status(session, "processed"))
        total_docs = len(DocumentRecordRepo.get_all(session))
        total_chunks = len(ChunkRecordRepo.get_all(session))

        typer.echo("=== Document Processing Status ===")
        typer.echo(f"Pending inputs: {pending_count}")
        typer.echo(f"Processed inputs: {processed_count}")
        typer.echo(f"Total documents: {total_docs}")
        typer.echo(f"Total chunks: {total_chunks}")

    finally:
        session.close()


if __name__ == "__main__":
    doc_processor_cli()
