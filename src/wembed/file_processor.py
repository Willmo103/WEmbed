import hashlib
import mimetypes
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional
from uuid import uuid4

import typer

from wembed.db.file_line import FileLineSchema

from .config import md_xref
from .db import (
    DocumentIndexRepo,
    DocumentIndexSchema,
    FileRecordRepo,
    FileRecordSchema,
    InputRecordRepo,
    InputRecordSchema,
    RepoRecordRepo,
    VaultRecordRepo,
)
from . import DBService


def create_file_record_from_path(
    file_path: Path,
    source_type: str,
    source_name: str,
    source_root: str,
    relative_path: str,
) -> Optional[FileRecordSchema]:
    """Create a FileRecordSchema from a file path."""
    if not file_path.is_file() or not file_path.exists():
        return None

    try:
        # Read file content
        with open(file_path, "rb") as f:
            content = f.read()

        # Try to decode as text
        try:
            content_text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_text = content.decode("latin-1", errors="replace")
            except Exception:
                content_text = "<Binary or non-text content>"

        # Calculate hashes
        sha256 = hashlib.sha256(content).hexdigest()
        md5 = hashlib.md5(content).hexdigest()

        # Get file stats
        stat = file_path.stat()

        # Count lines if it's a text file
        line_count = (
            len(content_text.splitlines())
            if content_text != "<Binary or non-text content>"
            else 0
        )

        file_record = FileRecordSchema(
            id=uuid4().hex,
            version=1,
            source_type=source_type,
            source_root=source_root,
            source_name=source_name,
            host=os.environ.get("COMPUTERNAME", "unknown"),
            user=os.environ.get("USERNAME", "unknown"),
            name=file_path.name,
            stem=file_path.stem,
            path=str(file_path),
            relative_path=relative_path,
            suffix=file_path.suffix,
            sha256=sha256,
            md5=md5,
            mode=stat.st_mode,
            size=stat.st_size,
            content=(
                content if len(content) < 1024 * 1024 else None
            ),  # Don't store large files in DB
            content_text=content_text,
            ctime_iso=datetime.fromtimestamp(stat.st_birthtime, tz=timezone.utc),
            mtime_iso=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            created_at=datetime.now(timezone.utc),
            line_count=line_count,
            uri=f"file://{file_path.as_posix()}",
            mimetype=mimetypes.guess_type(file_path.name)[0]
            or "application/octet-stream",
            markdown=None,  # Will be generated separately
        )

        return file_record

    except Exception as e:
        typer.secho(
            f"\nError creating file record for {file_path}: {e}, {traceback.format_exc()}\n",
            fg=typer.colors.RED,
        )
        return None


def get_filelines_list_from_file_record(
    file_record: FileRecordSchema,
) -> list[FileLineSchema]:
    """
    Genetates a list of FileLineSchema objects from a FileRecordSchema.
    returns [] if file_record.content_text is None or empty.
    """
    if not file_record.content_text:
        return []

    lines = file_record.content_text.splitlines()
    filelines = []
    for idx, line in enumerate(lines, start=1):
        fileline = FileLineSchema(
            id=uuid4().hex,
            file_id=file_record.id,
            line_number=idx,
            content=line,
            created_at=datetime.now(timezone.utc),
        )
        filelines.append(fileline)

    return filelines


def generate_markdown_content(file_record: FileRecordSchema) -> str:
    """Generate markdown content for a file record."""
    return f"""---
id: {file_record.id}
host: {file_record.host}
user: {file_record.user}
sha256: {file_record.sha256}
uri: {file_record.uri}
source_type: {file_record.source_type}
source_name: {file_record.source_name}
generated_at: {file_record.created_at.isoformat() if hasattr(file_record.created_at, 'isoformat') else file_record.created_at}
version: {file_record.version}
---

# {file_record.name} *(Version {file_record.version})*

## File Information

**URI:** `{file_record.uri}`

| Property                | Value                   |
|-------------------------|-------------------------|
| **Host** | `{file_record.host}`            |
| **User** | `{file_record.user}`            |
| **Source Type** | `{file_record.source_type}`          |
| **Source Name** | `{file_record.source_name}`          |
| **File Hash (sha256)** | `{file_record.sha256}`         |
| **File Hash (md5)** | `{file_record.md5}`            |
| **ID** | `{file_record.id}`              |
| **Full Path** | `{file_record.path}`        |
| **Relative Path** | `{file_record.relative_path}`            |
| **File Name** | `{file_record.name}`            |
| **File Stem** | `{file_record.stem}`            |
| **File Mode** | `{file_record.mode}`            |
| **File Suffix** | `{file_record.suffix}`          |
| **Size (bytes)** | `{file_record.size}`            |
| **Line Count** | `{file_record.line_count}`      |
| **MIME Type** | `{file_record.mimetype}`        |
| **Created At** | `{file_record.ctime_iso}`        |
| **Modified At** | `{file_record.mtime_iso}`        |
| **Indexed At** | `{file_record.created_at}`      |

---

## File Content

```{md_xref.get(file_record.suffix, "")}
{file_record.content_text or "<Binary or non-text content>"}
```
"""


def generate_markdown_content_from_path(
    file_path: Path,
    source_type: Optional[str] = "unknown",
    source_name: Optional[str] = "unknown",
) -> str:
    """Generate markdown content directly from a file path."""
    file_record = create_file_record_from_path(
        file_path,
        source_type=source_type,
        source_name=source_name,
        source_root=str(file_path.parent),
        relative_path=file_path.name,
    )
    if file_record:
        return generate_markdown_content(file_record)
    return "# Error generating markdown content"


def write_markdown_to_vault(file_record: FileRecordSchema, dir: Path) -> Path:
    """Write markdown content to the vault directory."""
    # Create the destination path in the vault
    dest_path = (
        dir
        / file_record.source_type
        / file_record.source_name
        / f"{file_record.relative_path}.md"
    )

    # Create parent directories
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the markdown file
    dest_path.write_text(file_record.markdown, encoding="utf-8")

    return dest_path


def get_vault_files(
    db_svc: DBService,
) -> Generator[tuple[Path, str, str, str], None, None]:
    """Generator that yields vault file information."""
    session = db_svc.get_session()
    try:
        vaults = VaultRecordRepo.get_all(session)
        for vault in vaults:
            vault_schema = VaultRecordRepo.to_schema(vault)
            for file_path in vault_schema.files or []:
                full_path = Path(vault_schema.root_path) / file_path
                yield full_path, "vault", vault_schema.name, vault_schema.root_path
    finally:
        session.close()


def get_repo_files(
    db_svc: DBService,
) -> Generator[tuple[Path, str, str, str], None, None]:
    """Generator that yields repo file information."""
    session = db_svc.get_session()
    try:
        repos = RepoRecordRepo.get_all(session)
        for repo in repos:
            repo_schema = RepoRecordRepo.to_schema(repo)
            for file_path in repo_schema.files or []:
                full_path = Path(repo_schema.root_path) / file_path
                yield full_path, "repo", repo_schema.name, repo_schema.root_path
    finally:
        session.close()


def process_vault_files(db_svc: DBService) -> None:
    """Process all vault files into FileRecords."""
    session = db_svc.get_session()
    processed_count = 0
    error_count = 0

    try:
        for (
            file_path,
            source_type,
            source_name,
            source_root,
        ) in get_vault_files():
            try:
                # Calculate relative path
                relative_path = str(file_path.relative_to(source_root))

                # Check if file record already exists
                existing = FileRecordRepo.get_by_sha256(
                    session, hashlib.sha256(file_path.read_bytes()).hexdigest()
                )
                if existing:
                    typer.echo(f"Skipping {file_path} - already processed")
                    continue

                # Create file record
                file_record = create_file_record_from_path(
                    file_path,
                    source_type,
                    source_name,
                    source_root,
                    relative_path,
                )

                if not file_record:
                    continue

                # Generate markdown
                markdown_content = generate_markdown_content(file_record)
                file_record.markdown = markdown_content

                # Save to database
                FileRecordRepo.create(session, file_record)

                # Write markdown to vault
                vault_path = write_markdown_to_vault(file_record, markdown_content)

                # Add to document index
                doc_index = DocumentIndexSchema(
                    file_id=file_record.id,
                    last_rendered=datetime.now(timezone.utc),
                )
                DocumentIndexRepo.create(session, doc_index)

                # Add to input processing queue
                input_record = InputRecordSchema(
                    source_type=source_type,
                    status="pending",
                    input_file_id=file_record.id,
                )
                InputRecordRepo.create(session, input_record)

                processed_count += 1
                typer.echo(f"Processed: {file_path} -> {vault_path}")

            except Exception as e:
                error_count += 1
                typer.secho(f"Error processing {file_path}: {e}", fg=typer.colors.RED)
                with open("file_processor_errors.log", "a", encoding="utf-8") as log:
                    log.write(
                        f"{datetime.now(tz=timezone.utc)} - Error processing {file_path}: {e}\n"
                    )
                    log.write(f"Traceback: {traceback.format_exc()}\n\n")

    finally:
        session.close()
        typer.echo(
            f"Vault processing complete. Processed: {processed_count}, Errors: {error_count}"
        )


def process_repo_files(db_svc: DBService) -> None:
    """Process all repo files into FileRecords."""
    session = db_svc.get_session()
    processed_count = 0
    error_count = 0

    try:
        for (
            file_path,
            source_type,
            source_name,
            source_root,
        ) in get_repo_files(db_svc):
            try:
                # Calculate relative path
                relative_path = str(file_path.relative_to(source_root))

                # Check if file record already exists
                if file_path.exists():
                    existing = FileRecordRepo.get_by_sha256(
                        session,
                        hashlib.sha256(file_path.read_bytes()).hexdigest(),
                    )
                    if existing:
                        typer.echo(f"Skipping {file_path} - already processed")
                        continue

                # Create file record
                file_record = create_file_record_from_path(
                    file_path,
                    source_type,
                    source_name,
                    source_root,
                    relative_path,
                )

                if not file_record:
                    continue

                # Generate markdown
                markdown_content = generate_markdown_content(file_record)
                file_record.markdown = markdown_content

                # Save to database
                FileRecordRepo.create(session, file_record)

                # Write markdown to vault
                vault_path = write_markdown_to_vault(file_record, markdown_content)

                # Add to document index
                doc_index = DocumentIndexSchema(
                    file_id=file_record.id,
                    last_rendered=datetime.now(timezone.utc),
                )
                DocumentIndexRepo.create(session, doc_index)

                # Add to input processing queue
                input_record = InputRecordSchema(
                    source_type=source_type,
                    status="pending",
                    input_file_id=file_record.id,
                )
                InputRecordRepo.create(session, input_record)

                processed_count += 1
                typer.echo(f"Processed: {file_path} -> {vault_path}")

            except Exception as e:
                error_count += 1
                typer.secho(f"Error processing {file_path}: {e}", fg=typer.colors.RED)
                with open("file_processor_errors.log", "a", encoding="utf-8") as log:
                    log.write(
                        f"{datetime.now().isoformat()} - Error processing {file_path}: {e}\n"
                    )
                    log.write(f"Traceback: {traceback.format_exc()}\n\n")

    finally:
        session.close()
        typer.echo(
            f"Repo processing complete. Processed: {processed_count}, Errors: {error_count}"
        )


# --- Typer CLI Application ---
