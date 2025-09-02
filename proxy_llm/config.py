import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    MOONSHOT_MODEL = os.getenv("MOONSHOT_MODEL", "kimi-k2-0711-preview")
    LOCAL_MODEL = os.getenv("LOCAL_MODEL", "gpt-oss-120b")
    LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL", "http://localhost:10003/v1")
    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "local")
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/proxy_logs.txt")
    LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", 10485760))
    SAVE_LOGS_TO_FILE = os.getenv("SAVE_LOGS_TO_FILE", "false").lower() == "true"

    # Цены
    PRICES = {
        "deepseek": {
            "input_cache_hit": 0.07 / 1_000_000,
            "input_cache_miss": 0.56 / 1_000_000,
            "output": 1.68 / 1_000_000
        },
        "moonshot": {
            "input_cache_hit": 0.15 / 1_000_000,
            "input_cache_miss": 0.60 / 1_000_000,
            "output": 2.50 / 1_000_000
        }
    }