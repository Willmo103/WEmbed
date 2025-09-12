from sqlalchemy import create_engine, Engine
from pathlib import Path
from typing import Any

from pydantic import computed_field
from sqlite_utils import Database
from constants import (
    MD_DB,
    REPO_DATABASE,
    MD_VAULT,
    STORAGE,
    EMBED_MODEL_ID,
    EMBED_MODEL_NAME,
    EMBEDDING_LENGTH,
    MAX_TOKENS,
    SQLITE_REPO_URI,
    SQLITE_MD_URI,
    HOST,
    USER,
    POSTGRES_URI,
    _md_db,
    _repo_db
)
from ignore_ext import IGNORE_EXTENSIONS
from ignore_parts import IGNORE_PARTS
from md_xref import MD_XREF
from headers import HEADERS

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    repo_db_pth: str = _repo_db.as_posix()
    md_db_pth: str = _md_db.as_posix()
    storage: Path = STORAGE
    md_vault: Path = MD_VAULT
    ignore_parts: list[str] = IGNORE_PARTS
    ignore_extensions: list[str] = IGNORE_EXTENSIONS
    md_xref: dict[str, str] = MD_XREF
    headers: dict[str, str] = HEADERS
    embed_model_id: str = EMBED_MODEL_ID
    embed_model_name: str = EMBED_MODEL_NAME
    embedding_length: int = EMBEDDING_LENGTH
    max_tokens: int = MAX_TOKENS
    host: str = HOST
    user: str = USER
    postgres_uri: str | None = POSTGRES_URI
    repo_db_uri: str = SQLITE_REPO_URI
    md_db_uri: str = SQLITE_MD_URI

    model_config = {
    }

    @computed_field
    def md_db(self) -> Database:
        return Database(self.md_db_pth)

    @computed_field
    def repo_db(self) -> Database:
        return Database(self.repo_db_pth)

    @computed_field
    def postgres_db(self) -> Engine | None:

        if self.postgres_uri:
            return create_engine(self.postgres_uri)
        return None


config = Config()
print(config.md_db.table_names())

eng = config.postgres_db
if eng is not None:
    with eng.connect() as conn:
        result = conn.execute("SELECT 1")
        print(result.fetchone())
else:
    print("Postgres database is not available.")
