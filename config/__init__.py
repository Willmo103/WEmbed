from sqlalchemy import create_engine, Engine, text
from pathlib import Path
from typing import Any
import psycopg2

from pydantic import computed_field
from sqlite_utils import Database
import typer
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
    _repo_db,
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
        "json_encoders": {
            Path: lambda v: v.as_posix(),
            Database: lambda v: str(v),
            Engine: lambda v: str(v),
        }
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


conf = Config()
config_cli = typer.Typer(
    name="config", no_args_is_help=True, help="Configuration commands"
)


def ppconfig_conf():
    print(conf.model_dump_json(indent=4))


def export_config(fp: str):
    fp = Path(fp).resolve() / "file_injester.config.json"
    with open(fp, "w") as f:
        f.write(
            conf.model_dump_json(indent=4, exclude={"md_db", "repo_db", "postgres_db"})
        )


@config_cli.command(name="show")
def show_config():
    ppconfig_conf()


@config_cli.command(name="export")
def export_config_command(
    fp: str = typer.Argument(
        ...,
        file_okay=False,
        dir_okay=True,
        exists=False,
        help="Directory to export config file to",
    )
):
    export_config(fp)


@config_cli.command(name="test-db", help="Test Postgres DB connection")
def test_db_connection():
    sql = "SELECT schema_name FROM information_schema.schemata"
    try:
        eng = create_engine(conf.postgres_uri)
        with eng.connect() as conn:
            conn.execute(text(sql))
        print("Repository database connection successful.")
    except psycopg2.Error as e:
        print(f"Repository database connection failed: {e}")

if __name__ == "__main__":
    config_cli()
