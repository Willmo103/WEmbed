# WEmbed Development Guide

WEmbed is a Python Context Engineering Library for LLMs, designed to scan, process, and index various file sources for retrieval and embedding generation. This guide will help you navigate the codebase and understand its key components.

## Architecture Overview

WEmbed follows a modular architecture:

1. **File Scanning**: `file_scanner.py` discovers and indexes files from repos, vaults, or lists.
2. **File Processing**: `file_processor.py` processes files, generating metadata and markdown representations.
3. **Document Processing**: `dl_doc_processor.py` converts files to DoclingDocuments, chunks content, and creates embeddings.
4. **Database Layer**: SQLAlchemy ORM models in `db/` folder store all records.
5. **Configuration**: Settings management in `config/` with environment variable overrides.
6. **CLI Commands**: Typer-based CLI with subcommands for each major function.

## Key Workflows

### Setup

```bash
# Install dependencies
pip install -e '.[dev,test]'

# Configure environment (create .env from example.env)
cp example.env .env
```

### Development

```bash
# Run tests
pytest

# Test coverage
pytest --cov=src/wembed

# CLI commands
python -m wembed.cli conf list  # List configuration
python -m wembed.cli idx repo   # Scan a repository
python -m wembed.cli proc       # Process files
python -m wembed.cli doc embed  # Create embeddings
```

## Project Conventions

1. **CLI Structure**: Commands are organized as Typer apps with subcommands (conf, idx, db, proc, doc).
2. **Database Models**: Each entity has its own file in `db/` with CRUD operations.
3. **Configuration**: Uses Pydantic with environment variables, managed through `config/__init__.py`.
4. **Path Handling**: All paths are normalized to `Path` objects with `.resolve()` for consistency.
5. **Error Handling**: Exceptions are caught, logged with traceback, and returned as user-friendly errors.

## Database Architecture

The ORM layer is built with SQLAlchemy and follows a consistent pattern:

1. **Model Definition**: Each entity (FileRecord, DocumentRecord, etc.) is defined as a SQLAlchemy model in its own file.
2. **Schema Definition**: Pydantic schemas (e.g., FileRecordSchema) validate data before database operations.
3. **CRUD Classes**: Each model has a companion CRUD class (e.g., FileRecordCRUD) with static methods for database operations.

Key components:
- `db/_base.py`: Contains the SQLAlchemy Base class used by all models
- `db/__init__.py`: Manages database connections and session creation
- `db/file_record.py`, `db/document_record.py`, etc.: Individual entity definitions

The session management functions handle both local SQLite and remote PostgreSQL databases:
- `get_session_local()`: Returns a session for the local SQLite database
- `get_session_remote()`: Returns a session for the remote PostgreSQL database (if configured)
- `get_session()`: Smart function that tries remote first, then falls back to local

## Cross-Component Communication

1. **Data Flow**: scan → process → document → embed
2. **Integration Points**:
   - `file_scanner.py` discovers files and stores results in database
   - `file_processor.py` reads scan results and creates `FileRecord` entries
   - `dl_doc_processor.py` processes files into documents with embeddings

## Key Files

- `src/wembed/cli.py`: Entry point with all subcommands
- `src/wembed/enums.py`: Source and scan type enumerations
- `src/wembed/schemas.py`: Pydantic models for data validation
- `src/wembed/config/__init__.py`: Configuration management
- `src/wembed/db/_base.py`: SQLAlchemy Base class

## External Dependencies

- **Document Processing**: Relies on `docling` and `docling_core` for document conversion and chunking
- **Embeddings**: Uses `llm` and `llm-ollama` for embedding generation
- **Database**: SQLAlchemy with SQLite for storage
- **CLI**: Typer for command-line interface

## Debugging Tips

1. Set `APP_STORAGE` environment variable to change data storage location
2. Use `MAX_FILE_SIZE` to control which files are fully stored (default 3MB)
3. Check `data/local.db` for indexed content
4. When processing large repositories, use targeted scans with appropriate filters

## Testing Strategy

The project follows a comprehensive testing approach focused on isolation and coverage:

1. **Test Data Isolation**: Tests use temporary directories and databases via the `temp_dir` and `temp_config` fixtures in `conftest.py`.

2. **Database Testing Patterns**:
   - **Model Tests**: Verify model fields, relationships, and constraints
   - **CRUD Tests**: Test create, read, update, and delete operations
   - **Schema Tests**: Validate Pydantic schema validation and conversion
   - **Session Tests**: Verify database connection and session management

3. **Mocking External Dependencies**:
   ```python
   @patch('src.wembed.db.create_engine')
   def test_db_connection(mock_create_engine):
       # Mock the database engine
       mock_engine = mock_create_engine.return_value
       mock_conn = mock_engine.connect.return_value
       mock_conn.__enter__.return_value = mock_conn

       # Test the function
       assert test_db_connection() is True
   ```

4. **Test Coverage Goals**:
   - All database models and CRUD operations (100% coverage)
   - Configuration management and environment variable handling
   - File scanning and processing logic
   - Error handling and recovery mechanisms

5. **Running Tests with Coverage**:
   ```bash
   # Run all tests with coverage reporting
   pytest --cov=src/wembed --cov-report=html

   # Test specific modules
   pytest --cov=src/wembed/db tests/test_db.py

   # Examine uncovered lines
   pytest --cov=src/wembed/db --cov-report=term-missing tests/test_db.py
   ```
