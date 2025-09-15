from enum import Enum


class SourceTypes(str, Enum):
    REPO = "repo"
    VAULT = "vault"
    DOCUMENTATION = "documentation"
    WEB = "web"
    AI_RESPONSE = "ai_response"
    MD_FILE_TMP = "md_file_tmp"
    REPO_MD_FILE = "repo_md_file"
    VAULT_FILE = "vault_file"


class ScanTypes(str, Enum):
    REPO = "repo"
    VAULT = "vault"
    LIST = "list"
