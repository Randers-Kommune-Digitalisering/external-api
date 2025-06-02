import sqlalchemy
import logging


class DatabaseClient:
    def __init__(self, db_type, database, username, password, host, port=None):
        if db_type.lower() == 'mssql':
            driver = 'mssql+pymssql'
        elif db_type.lower() == 'mariadb':
            driver = 'mariadb+mariadbconnector'
        elif db_type.lower() == 'postgresql':
            driver = 'postgresql+psycopg2'
        else:
            raise ValueError(f"Invalid database type {type}")

        self.logger = logging.getLogger(__name__)

        if port:
            host = host + f':{port}'

        self.engine = sqlalchemy.create_engine(f'{driver}://{username}:{password}@{host}/{database}')

    def get_connection(self):
        try:
            if self.engine:
                return self.engine.connect()
            self.logger.error("DatabaseClient not initialized properly. Engine is None. Check error from init.")
        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")

    def execute_sql(self, sql):
        try:
            with self.get_connection() as conn:
                return conn.execute(sqlalchemy.text(sql))
        except Exception as e:
            self.logger.error(f"Error executing SQL: {e}")
