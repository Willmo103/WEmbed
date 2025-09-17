from sqlalchemy import create_engine, Engine
from pathlib import Path

from pydantic import computed_field
from sqlite_utils import Database
import typer
from .constants import (
    MD_VAULT,
    STORAGE,
    EMBED_MODEL_HF_ID,
    EMBED_MODEL_NAME,
    EMBEDDING_LENGTH,
    MAX_TOKENS,
    LOCAL_DB_URI,
    HOST,
    USER,
    POSTGRES_URI,
    local_db_path,
    VAULT_FOLDER,
    VAULT_EXTENSIONS,
)
from .ignore_ext import IGNORE_EXTENSIONS
from .ignore_parts import IGNORE_PARTS
from .md_xref import MD_XREF
from .headers import HEADERS

from pydantic_settings import BaseSettings


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
