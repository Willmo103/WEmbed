from .constants import (
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
)
from ignore_ext import IGNORE_EXTENSIONS
from ignore_parts import IGNORE_PARTS
from md_xref import MD_XREF
from headers import HEADERS

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    md_db: str = SQLITE_MD_URI
    repo_db: str = SQLITE_REPO_URI
    storage: str = STORAGE
    md_vault: str = MD_VAULT
    ignore_parts: list[str] = IGNORE_PARTS
    ignore_extensions: list[str] = IGNORE_EXTENSIONS
    md_xref: dict[str, str] = MD_XREF
    headers: dict[str, str] = HEADERS
    embed_model_id: str = EMBED_MODEL_ID
    embed_model_name: str = EMBED_MODEL_NAME
    embedding_length: int = EMBEDDING_LENGTH
    max_tokens: int = MAX_TOKENS
    sl_utils_repo_db: str = REPO_DATABASE
    sl_utils_md_db: str = MD_DB
    host: str = HOST
    user: str = USER
    postgres_uri: str = POSTGRES_URI

    model_config = {
        "arbitrary_types_allowed": True,
        "from_attributes": True
    }
