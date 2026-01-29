#!/usr/bin/env python3
"""
Скрипт для запуска сервера LLM Proxy в фоне с настройками из config и env.
Запускает сервер напрямую через uvicorn (без подпроцесса).
"""

import sys
import signal
import logging
import asyncio
from contextlib import asynccontextmanager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорт приложения и конфигурации
try:
    from server import app
    from config import config as Config
except ImportError as e:
    logger.error(f"Ошибка импорта модулей: {e}")
    logger.error("Убедитесь, что все зависимости установлены и модули находятся в PYTHONPATH")
    sys.exit(1)

@asynccontextmanager
async def lifespan(app):
    """
    Lifespan менеджер для обработки событий запуска и остановки сервера.
    """
    # Код запуска
    logger.info("Инициализация сервера LLM Proxy...")
    
    # Получаем настройки провайдеров
    providers = Config.get_providers()
    default_provider = Config.get_default_provider()
    logger.info(f"Доступные провайдеры: {list(providers.keys())}")
    logger.info(f"Провайдер по умолчанию: {default_provider}")
    
    # Выводим информацию о моделях
    for provider_name, provider_config in providers.items():
        if provider_config.get("enabled", False):
            models = provider_config.get("models", [])
            if models:
                model_names = [model["name"] for model in models]
                logger.info(f"  {provider_name}: модели {', '.join(model_names)}")
    
    yield
    
    # Код остановки
    logger.info("Завершение работы сервера...")

# Добавляем lifespan к приложению
app.router.lifespan_context = lifespan

def run_server():
    """Запуск сервера"""
    logger.info("Запуск LLM Proxy сервера...")
    
    # Получаем конфигурацию сервера
    server_config = Config.get_server_config()
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)
    
    logger.info(f"Сервер будет запущен на {host}:{port}")
    logger.info(f"Доступен по адресу: http://localhost:{port}")
    logger.info("Для остановки нажмите Ctrl+C или отправьте SIGTERM")
    
    try:
        import uvicorn
        
        # Конфигурация uvicorn
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            lifespan="on"
        )
        server = uvicorn.Server(config)
        
        # Устанавливаем обработчик сигналов для graceful shutdown
        import signal
        
        def handle_signal(signum, frame):
            logger.info(f"Получен сигнал {signum}, останавливаю сервер...")
            server.should_exit = True
            
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)
        
        # Запуск сервера
        asyncio.run(server.serve())
        
    except KeyboardInterrupt:
        logger.info("\nПолучен сигнал прерывания (Ctrl+C)")
        logger.info("Остановка сервера...")
    except Exception as e:
        logger.error(f"Ошибка при запуске сервера: {e}")
        sys.exit(1)
    finally:
        logger.info("Сервер остановлен")

if __name__ == "__main__":
    run_server()