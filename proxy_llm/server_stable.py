#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import logging
import asyncio
from providers.deepseek import DeepSeekProvider
from providers.moonshot import MoonshotProvider
from providers.local import LocalProvider
from utils.token_counter import TokenCounter
from config import Config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Middleware для логирования
@app.middleware("http")
async def log_requests(request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    logger.info(f"🔍 Request from {client_ip}: {request.method} {request.url}")
    logger.info(f"🔍 Headers: {dict(request.headers)}")
    
    # Только логируем информацию о теле, но не читаем его
    if request.method == "POST":
        content_length = request.headers.get("content-length", "unknown")
        logger.info(f"🔍 Content-Length: {content_length}")

    try:
        response = await call_next(request)
        logger.info(f"✅ Response: {response.status_code}")
        logger.info(f"✅ Response headers: {dict(response.headers)}")
        return response
    except Exception as e:
        logger.error(f"❌ Error in request processing: {e}")
        raise

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Провайдеры
providers = {}
if Config.DEEPSEEK_API_KEY and Config.DEEPSEEK_API_KEY != "sk-ваш-ключ-здесь":
    providers["deepseek"] = DeepSeekProvider()
    logger.info("DeepSeek provider initialized")
if Config.MOONSHOT_API_KEY:
    providers["moonshot"] = MoonshotProvider()
    logger.info("Moonshot provider initialized")

# Всегда добавляем локальный провайдер
providers["local"] = LocalProvider()
logger.info("Local provider initialized")

current_provider = Config.DEFAULT_PROVIDER if Config.DEFAULT_PROVIDER in providers else "local"
token_counter = TokenCounter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

@app.get("/")
async def root():
    return {"message": "LLM Proxy Server running", "provider": current_provider}

@app.get("/health")
async def health():
    return {"status": "healthy", "provider": current_provider}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    logger.info("🎯 === FUNCTION STARTED ===")
    logger.info("=== START PROCESSING ===")
    
    # Читаем тело запроса вручную
    body = await request.body()
    body_str = body.decode('utf-8', errors='ignore') if body else "empty"
    logger.info(f"🔍 Raw request body: {body_str}")
    
    # Пытаемся распарсить JSON
    import json
    try:
        data = json.loads(body_str)
        logger.info(f"✅ JSON parsed successfully: {data}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    logger.info("Returning immediate test response")
    
    try:
        # Просто возвращаем тестовый ответ для отладки
        logger.info("Returning test response")
        return {
            "id": "test-id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": data.get("model", "unknown-model"),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from stable server"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }
        
    except Exception as e:
        logger.error(f"Error in chat_completions: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Добавляем обработчик для отлова ошибок валидации Pydantic
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    body = await request.body()
    body_str = body.decode('utf-8', errors='ignore') if body else "empty"
    logger.error(f"❌ Pydantic validation error: {exc}")
    logger.error(f"❌ Request body: {body_str}")
    logger.error(f"❌ Error details: {exc.errors()}")
    logger.error(f"❌ Error type: {type(exc)}")
    
    # Добавляем дополнительную диагностику
    import json
    try:
        parsed_body = json.loads(body_str) if body_str != "empty" else {}
        logger.error(f"❌ Parsed JSON: {parsed_body}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error: {e}")
    
    return JSONResponse(
        status_code=400,  # Меняем на 400, так как клиенты ожидают этот код
        content={"detail": exc.errors(), "body": body_str}
    )

# Добавляем глобальный обработчик исключений
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Global exception: {exc}")
    logger.error(f"❌ Exception type: {type(exc)}")
    import traceback
    logger.error(f"❌ Traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": str(type(exc))}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10005)