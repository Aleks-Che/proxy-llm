import os
import json
from typing import Dict, Any

class Config:
    _settings = None

    @classmethod
    def load_settings(cls):
        if cls._settings is None:
            settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    cls._settings = json.load(f)
            except FileNotFoundError:
                # Fallback to default settings if file doesn't exist
                cls._settings = cls._get_default_settings()
            except json.JSONDecodeError:
                print("Error parsing settings.json, using defaults")
                cls._settings = cls._get_default_settings()

    @classmethod
    def _get_default_settings(cls):
        return {
            "providers": {
                "deepseek": {
                    "api_key": "",
                    "models": [{"name": "deepseek-chat", "context_window": 128000, "pricing": {"input_cache_hit": 0.07, "input_cache_miss": 0.56, "output": 1.68}}],
                    "base_url": "https://api.deepseek.com",
                    "enabled": True
                },
                "local": {
                    "api_key": "",
                    "models": [{"name": "gpt-oss-120b", "context_window": 128000, "pricing": {"input_cache_hit": 0.0, "input_cache_miss": 0.0, "output": 0.0}}],
                    "base_url": "http://localhost:10003/v1",
                    "enabled": True
                },
                "minimax": {
                    "api_key": "",
                    "models": [{"name": "MiniMax-M2.1", "context_window": 192000, "pricing": {"input_cache_hit": 0.0, "input_cache_miss": 0.0, "output": 0.0}}],
                    "base_url": "https://api.minimax.chat/v1",
                    "enabled": True
                }
            },
            "default_provider": "local",
            "server": {"host": "0.0.0.0", "port": 8000},
            "logging": {"save_to_file": False, "file_path": "logs/proxy_logs.txt", "max_size": 10485760},
            "language": "en"
        }

    @classmethod
    def save_settings(cls):
        settings_path = os.path.join(os.path.dirname(__file__), 'settings.json')
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(cls._settings, f, indent=2, ensure_ascii=False)

    @classmethod
    def get_providers(cls) -> Dict[str, Any]:
        cls.load_settings()
        return cls._settings.get("providers", {})

    @classmethod
    def get_provider_config(cls, provider_name: str) -> Dict[str, Any]:
        providers = cls.get_providers()
        return providers.get(provider_name, {})

    @classmethod
    def get_default_provider(cls) -> str:
        cls.load_settings()
        return cls._settings.get("default_provider", "local")

    @classmethod
    def get_server_config(cls) -> Dict[str, Any]:
        cls.load_settings()
        return cls._settings.get("server", {"host": "0.0.0.0", "port": 8000})

    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        cls.load_settings()
        return cls._settings.get("logging", {"save_to_file": False, "file_path": "logs/proxy_logs.txt", "max_size": 10485760})

    @classmethod
    def get_language(cls) -> str:
        cls.load_settings()
        return cls._settings.get("language", "en")

    @classmethod
    def get_max_tokens(cls) -> int:
        cls.load_settings()
        return cls._settings.get("max_tokens", 8000)

    @classmethod
    def get_model_max_tokens(cls, provider_name: str, model_name: str = None) -> int:
        """
        Получить max_tokens для конкретной модели.
        Если model_name не указан, возвращает max_tokens первой модели провайдера.
        """
        cls.load_settings()
        provider_config = cls.get_provider_config(provider_name)
        models = provider_config.get("models", [])
        
        if not models:
            return cls.get_max_tokens()
        
        if model_name:
            for model in models:
                if model.get("name") == model_name:
                    return model.get("max_tokens", cls.get_max_tokens())
        
        # Если модель не найдена, возвращаем max_tokens первой модели
        return models[0].get("max_tokens", cls.get_max_tokens())

    # Legacy properties for backward compatibility
    @property
    def MAX_TOKENS(self):
        return self.get_max_tokens()

    @property
    def DEEPSEEK_API_KEY(self):
        return self.get_provider_config("deepseek").get("api_key", "")

    @property
    def MOONSHOT_API_KEY(self):
        return self.get_provider_config("moonshot").get("api_key", "")

    @property
    def MINIMAX_API_KEY(self):
        return self.get_provider_config("minimax").get("api_key", "")

    @property
    def DEEPSEEK_MODEL(self):
        models = self.get_provider_config("deepseek").get("models", [])
        return models[0]["name"] if models else "deepseek-chat"

    @property
    def MOONSHOT_MODEL(self):
        models = self.get_provider_config("moonshot").get("models", [])
        return models[0]["name"] if models else "kimi-k2-0711-preview"

    @property
    def MINIMAX_MODEL(self):
        models = self.get_provider_config("minimax").get("models", [])
        return models[0]["name"] if models else "MiniMax-M2.1"

    @property
    def LOCAL_MODEL(self):
        models = self.get_provider_config("local").get("models", [])
        return models[0]["name"] if models else "gpt-oss-120b"

    @property
    def LOCAL_BASE_URL(self):
        return self.get_provider_config("local").get("base_url", "http://localhost:10003/v1")

    @property
    def DEFAULT_PROVIDER(self):
        return self.get_default_provider()

    @property
    def SERVER_HOST(self):
        return self.get_server_config().get("host", "0.0.0.0")

    @property
    def SERVER_PORT(self):
        return self.get_server_config().get("port", 8000)

    @property
    def LOG_FILE_PATH(self):
        return self.get_logging_config().get("file_path", "logs/proxy_logs.txt")

    @property
    def LOG_MAX_SIZE(self):
        return self.get_logging_config().get("max_size", 10485760)

    @property
    def SAVE_LOGS_TO_FILE(self):
        return self.get_logging_config().get("save_to_file", False)

    @property
    def PRICES(self):
        providers = self.get_providers()
        prices = {}
        for provider_name, provider_config in providers.items():
            if provider_config.get("enabled", False):
                models = provider_config.get("models", [])
                if models:
                    # Use pricing from first model
                    pricing = models[0].get("pricing", {})
                    prices[provider_name] = {
                        "input_cache_hit": pricing.get("input_cache_hit", 0.0) / 1_000_000,
                        "input_cache_miss": pricing.get("input_cache_miss", 0.0) / 1_000_000,
                        "output": pricing.get("output", 0.0) / 1_000_000
                    }
        return prices

# Create singleton instance for backward compatibility
config = Config()