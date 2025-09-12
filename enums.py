from enum import Enum


class SourceTypes(str, Enum):
    REPO = "repo"
    VAULT = "vault"
    DOCUMENTATION = "documentation"
    WEB = "web"
    AI_RESPONSE = "ai_response"
    MD_FILE_TMP = "md_file_tmp"
