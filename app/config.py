from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: str  # Vergul bilan ajratilgan ID'lar
    CHANNEL_ID: int
    
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    
    REDIS_HOST: str
    REDIS_PORT: int

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def admins(self) -> List[int]:
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]

settings = Settings()
