from wembed.config import AppConfig
from wembed.db import DBService

cli_config = AppConfig()
cli_db_service = DBService(cli_config)

