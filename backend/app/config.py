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
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    public_demo_posts_per_minute: int = 20
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore", case_sensitive=False)

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            # Managed PostgreSQL services usually provide postgresql:// URLs;
            # this app uses psycopg v3 explicitly.
            if self.database_url.startswith("postgres://"):
                return self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
            if self.database_url.startswith("postgresql://"):
                return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
            return self.database_url
        if not self.postgres_user or not self.postgres_password:
            raise ValueError("PostgreSQL credentials are missing; configure POSTGRES_USER and POSTGRES_PASSWORD in backend/.env")
        return URL.create("postgresql+psycopg", username=self.postgres_user, password=self.postgres_password, host=self.postgres_host, port=self.postgres_port, database=self.postgres_db).render_as_string(hide_password=False)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

settings = Settings()
