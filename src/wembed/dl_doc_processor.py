# dl_doc_processor.py

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import llm
import typer
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from docling_core.types.doc.document import DoclingDocument

from wembed.cli.doc_processor_cli import doc_processor_cli

from .config import AppConfig
from .db import (
    ChunkRecordRepo,
    ChunkRecordSchema,
    DocumentRecordRepo,
    DocumentRecordSchema,
    FileRecordRepo,
    InputRecordRepo,
    get_session,
)

MAX_PROCESSING_SIZE = 1024 * 1024 * 3  # 3 MB


class DlDocProcessor:
    """Document processor for converting files to DoclingDocuments and creating embeddings."""

    def __init__(self, config: AppConfig):
        self._embedder = llm.get_embedding_model(config.embed_model_name)
        self._tokenizer = HuggingFaceTokenizer.from_pretrained(
            config.embed_model_id, config.max_tokens
        )
        self._converter = DocumentConverter()
        self._headers = config.headers
        self._chunker = HybridChunker(
            tokenizer=self._tokenizer,
        )
        self._collection = llm.Collection(
            name="chunk_embeddings",
            model=self._embedder,
            db=config.local_db,
        )

    def _convert_webpage(
        self, src: str, headers: Optional[dict] = None
    ) -> DoclingDocument:
        """Convert a webpage URL to a DoclingDocument."""
        return self._converter.convert(
            source=src, headers=headers if headers else self._headers
        ).document

    def _convert_md_file(self, src: str) -> DoclingDocument:
        """Convert a markdown file to a DoclingDocument."""
        return self._converter.convert(source=src).document

    def convert_source(
        self, src: str, input_record_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Convert a source (URL or file path) to a DoclingDocument and process chunks.

        Args:
            src: Source URL or file path
            input_record_id: Optional input record ID for tracking

        Returns:
            Document record ID if successful, None if failed
        """
        session = get_session()

        try:
            # Convert source to DoclingDocument
            if src.startswith("http"):
                typer.echo(f"Converting webpage: {src}")
                doc = self._convert_webpage(src, headers=self._headers)
                source_type = "web"
            else:
                typer.echo(f"Converting file: {src}")
                doc = self._convert_md_file(src)
                source_type = "file"

            if not doc:
                typer.secho(f"Failed to convert source: {src}", fg=typer.colors.RED)
                if input_record_id:
                    InputRecordRepo.add_error(
                        session,
                        input_record_id,
                        f"Failed to convert source: {src}",
                    )
                return None

            typer.echo(f"Successfully converted source: {src}")

            # Create document record
            doc_record = DocumentRecordSchema(
                source=src,
                source_type=source_type,
                source_ref=input_record_id,
                dl_doc=doc.model_dump_json(),
                markdown=doc.export_to_markdown(),
                html=doc.export_to_html(),
                text=doc.export_to_text(),
                doctags=doc.export_to_doctags(),
                chunks_json=None,
                created_at=datetime.now(timezone.utc),
            )

            # Save document record to get ID
            db_doc_record = DocumentRecordRepo.create(session, doc_record)
            doc_id = db_doc_record.id
            typer.echo(f"Created document record with ID: {doc_id}")

            # Process chunks
            chunks_data = []
            errors = []

            try:
                chunks = self._chunker.chunk(doc)
                total_chunks = len(list(chunks))
                typer.echo(f"Processing {total_chunks} chunks...")

                # Re-chunk since chunks iterator is consumed
                chunks = self._chunker.chunk(doc)

                for i, chunk in enumerate(chunks):
                    try:
                        typer.echo(f"Processing chunk {i + 1}/{total_chunks}", nl=False)
                        typer.echo("\r", nl=False)  # Carriage return for overwrite

                        # Contextualize chunk
                        c_txt = self._chunker.contextualize(chunk)
                        chunk.text = c_txt

                        # Add to chunks_json
                        chunks_data.append(chunk.model_dump_json())

                        # Generate embedding
                        embedding = self._embedder.embed(c_txt)

                        # Create chunk record
                        chunk_record = ChunkRecordSchema(
                            document_id=doc_id,
                            idx=i,
                            text_chunk=c_txt,
                            embedding=embedding,
                            created_at=datetime.now(timezone.utc),
                        )

                        # Save chunk record
                        ChunkRecordRepo.create(session, chunk_record)

                        # Add to collection for vector search
                        self._collection.embed(
                            id=f"{doc_id}_{i}",
                            value=c_txt,
                            metadata={"chunk_idx": i, "document_id": doc_id},
                            store=True,
                        )

                    except Exception as e:
                        error_msg = f"Error processing chunk {i}: {str(e)}"
                        errors.append(error_msg)
                        typer.secho(
                            f"\nError on chunk {i}: {e}",
                            fg=typer.colors.YELLOW,
                        )

                chunks_data = str([chunk.model_dump_json() for chunk in chunks])
                # Update document with chunks_json
                DocumentRecordRepo.update_chunks(session, doc_id, chunks_data)

                typer.echo(
                    f"\nProcessed {total_chunks - len(errors)} chunks successfully"
                )
                if errors:
                    typer.secho(
                        f"Encountered {len(errors)} errors during chunk processing",
                        fg=typer.colors.YELLOW,
                    )

            except Exception as e:
                error_msg = f"Error during chunking: {str(e)}"
                errors.append(error_msg)
                typer.secho(f"Chunking failed: {e}", fg=typer.colors.RED)

            # Update input record if provided
            if input_record_id:
                if errors:
                    # Add errors but mark as processed
                    for error in errors:
                        InputRecordRepo.add_error(session, input_record_id, error)

                InputRecordRepo.mark_processed(session, input_record_id, doc_id)
                typer.echo(f"Updated input record {input_record_id}")

            return doc_id

        except Exception as e:
            error_msg = f"Error occurred during conversion: {str(e)}"
            typer.secho(error_msg, fg=typer.colors.RED)

            if input_record_id:
                InputRecordRepo.add_error(session, input_record_id, error_msg)

            return None

        finally:
            session.close()

    def process_file_record(self, file_record_id: str) -> Optional[int]:
        """Process a file record by converting its markdown to a document."""
        session = get_session()

        try:
            # Get file record
            file_record_db = FileRecordRepo.get_by_id(session, file_record_id)
            if not file_record_db:
                typer.secho(
                    f"File record {file_record_id} not found",
                    fg=typer.colors.RED,
                )
                return None

            file_record = FileRecordRepo.to_schema(file_record_db)

            # Check if we have markdown content
            if not file_record.markdown:
                typer.secho(
                    f"No markdown content for file {file_record_id}",
                    fg=typer.colors.YELLOW,
                )
                return None

            if file_record.size and file_record.size > MAX_PROCESSING_SIZE:
                typer.secho(
                    f"File {file_record_id} exceeds maximum processing size",
                    fg=typer.colors.YELLOW,
                )
                return None

            # Create a temporary markdown file
            temp_md_path = Path(f"/tmp/temp_{file_record_id}.md")
            temp_md_path.parent.mkdir(parents=True, exist_ok=True)
            temp_md_path.write_text(file_record.markdown, encoding="utf-8")

            try:
                # Find associated input record
                input_record_db = InputRecordRepo.get_by_file_id(
                    session, file_record_id
                )
                input_record_id = int(input_record_db.id) if input_record_db else None

                # Convert the markdown file
                result = self.convert_source(str(temp_md_path), input_record_id)
                if result:
                    InputRecordRepo.mark_processed(session, input_record_id, result)
                return result

            finally:
                # Clean up temp file
                if temp_md_path.exists():
                    temp_md_path.unlink()

        except Exception as e:
            typer.secho(
                f"Error processing file record {file_record_id}: {e}",
                fg=typer.colors.RED,
            )
            return None

        finally:
            session.close()

    def process_pending_inputs(self) -> None:
        """Process all pending input records."""
        session = get_session()

        try:
            pending_inputs = InputRecordRepo.get_unprocessed(session)
            total_pending = len(pending_inputs)

            if not pending_inputs:
                typer.echo("No pending inputs to process")
                return

            typer.echo(f"Processing {total_pending} pending inputs...")

            processed_count = 0
            error_count = 0

            for i, input_record_db in enumerate(pending_inputs):
                input_record = InputRecordRepo.to_schema(input_record_db)
                typer.echo(
                    f"Processing input {i + 1}/{total_pending} (ID: {input_record.id})"
                )

                try:
                    if input_record.input_file_id:
                        # Process file-based input
                        result = self.process_file_record(input_record.input_file_id)
                        if result:
                            processed_count += 1
                        else:
                            error_count += 1
                    else:
                        typer.secho(
                            f"Input record {input_record.id} has no file ID",
                            fg=typer.colors.YELLOW,
                        )
                        error_count += 1

                except Exception as e:
                    typer.secho(
                        f"Error processing input {input_record.id}: {e}",
                        fg=typer.colors.RED,
                    )
                    InputRecordRepo.add_error(session, input_record.id, str(e))
                    error_count += 1

            typer.echo(
                f"Processing complete. Processed: {processed_count}, Errors: {error_count}"
            )

        finally:
            session.close()
