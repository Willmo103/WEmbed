from pathlib import Path

from .headers import HEADERS
from .ignore_ext import IGNORE_EXTENSIONS
from .ignore_parts import IGNORE_PARTS
from .md_xref import MD_XREF

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROD_CONFIG_DIR = Path.home() / ".wembed"
