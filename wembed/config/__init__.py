import os
from pathlib import Path

import typer
from pydantic import computed_field
from pydantic_settings import BaseSettings
from sqlalchemy import Engine, create_engine
from sqlite_utils import Database

from .constants import (
    EMBED_MODEL_HF_ID,
    EMBED_MODEL_NAME,
    EMBEDDING_LENGTH,
    HOST,
    LOCAL_DB_URI,
    MAX_TOKENS,
    MD_VAULT,
    POSTGRES_URI,
    STORAGE,
    USER,
    VAULT_EXTENSIONS,
    VAULT_FOLDER,
    local_db_path,
)
from .headers import HEADERS
from .ignore_ext import IGNORE_EXTENSIONS
from .ignore_parts import IGNORE_PARTS
from .md_xref import MD_XREF

os.environ["OLLAMA_HOST"] = "http://192.168.0.182:11434"


class Config(BaseSettings):
    db_path: str = local_db_path.as_posix()
    remote_db_uri: str | None = POSTGRES_URI
    local_db_uri: str = LOCAL_DB_URI
    md_vault: Path = MD_VAULT
    app_storage: Path = STORAGE
    ignore_parts: list[str] = IGNORE_PARTS
    ignore_extensions: list[str] = IGNORE_EXTENSIONS
    md_xref: dict[str, str] = MD_XREF
    headers: dict[str, str] = HEADERS
    embed_model_id: str = EMBED_MODEL_HF_ID
    embed_model_name: str = EMBED_MODEL_NAME
    embedding_length: int = EMBEDDING_LENGTH
    max_tokens: int = MAX_TOKENS
    host: str = HOST
    user: str = USER
    vault_folder: str = VAULT_FOLDER
    vault_extensions: set[str] = VAULT_EXTENSIONS

    model_config = {
        "json_encoders": {
            Path: lambda v: v.as_posix(),
            Database: lambda v: str(v),
            Engine: lambda v: str(v),
        }
    }

    @computed_field
    def local_db(self) -> Database:
        return Database(self.db_path)

    @computed_field
    def postgres_db(self) -> Engine | None:

        if self.remote_db_uri:
            return create_engine(self.remote_db_uri)
        return None


app_config = Config()
config_cli = typer.Typer(
    name="config", no_args_is_help=True, help="Configuration commands"
)


def ppconfig_conf():
    print(app_config.model_dump_json(indent=4))


def export_config(fp: str):
    fp = Path(fp).resolve() / "file_injester.config.json"
    with open(fp, "w") as f:
        f.write(
            app_config.model_dump_json(
                indent=4, exclude={"md_db", "repo_db", "postgres_db"}
            )
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


if __name__ == "__main__":
    config_cli()
