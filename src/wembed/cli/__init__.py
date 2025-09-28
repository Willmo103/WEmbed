from wembed.config import AppConfig
from wembed.services.db_service import DBService

cli_config = AppConfig()
cli_db_service = DBService(cli_config)
