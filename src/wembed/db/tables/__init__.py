"""
The `Tables` module encapsulates database tables that are not directly ment to be exposed directly, but
are used internally by the application.

Tables included:
- MdXrefTable: Stores the mapping between markdown file extensions and their corresponding markdown hilighting reference names.
- IgnoreExtTable: Stores file extensions that should be ignored during processing, preloaded from config.ignore_exts.IGNORE_EXTS.
- IgnorePartsTable: Stores parts of filenames that should be ignored during processing, preloaded from config.ignore_parts.IGNORE_PARTS.

Each table has an associated Pydantic schema for data validation and serialization.
These tables are not currently in use in the application.
They are included for potential future use for tracking user modifications to the Ignore configurations.
"""

from .ignore_ext_table import IgnoreExtSchema, IgnoreExtTable
from .ignore_parts_table import IgnorePartsSchema, IgnorePartsTable
from .md_xref_table import MdXrefSchema, MdXrefTable

__all__ = [
    "MdXrefTable",
    "MdXrefSchema",
    "IgnoreExtTable",
    "IgnoreExtSchema",
    "IgnorePartsTable",
    "IgnorePartsSchema",
]
