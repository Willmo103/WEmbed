from wembed.config import AppConfig
from wembed.services.db_service import DbService

cli_config = AppConfig()
cli_db_service = DbService(cli_config)
