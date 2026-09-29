from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

class Settings(BaseSettings):
    blockchain_rpc_url: str = "http://127.0.0.1:8545"
    landchain_contract_address: str = ""
    blockchain_private_key: str = ""
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "landchain"
    database_url: str | None = None
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore", case_sensitive=False)

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url: return self.database_url
        if not self.postgres_user or not self.postgres_password:
            raise ValueError("PostgreSQL credentials are missing; configure POSTGRES_USER and POSTGRES_PASSWORD in backend/.env")
        return URL.create("postgresql+psycopg", username=self.postgres_user, password=self.postgres_password, host=self.postgres_host, port=self.postgres_port, database=self.postgres_db).render_as_string(hide_password=False)

settings = Settings()
