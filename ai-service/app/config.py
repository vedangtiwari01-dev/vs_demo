import os
from typing import Optional

class Settings:
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    PORT: int = int(os.getenv('PORT', 8000))

settings = Settings()
