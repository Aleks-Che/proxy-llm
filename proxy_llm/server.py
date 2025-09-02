
from fastapi import FastAPI, HTTPException
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

@app.get("/test")
async def test():
    """Быстрый тест провайдера"""
    try:
        provider = providers[current_provider]
        messages = [{"role": "user", "content": "test"}]
        response = await provider.chat_completion(messages, max_tokens=5)
        return {"status": "ok", "response": response.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    logger.info("=== START PROCESSING ===")
    logger.info(f"Model requested: {request.model}")
    logger.info(f"Messages count: {len(request.messages) if request.messages else 0}")
    logger.info(f"Stream: {request.stream}")
    logger.info(f"Current provider: {current_provider}")
    
    try:
        provider = providers[current_provider]
        logger.info(f"Using provider: {current_provider}")
        
        # Обработка сообщений
        messages = []
        if request.messages:
            logger.info(f"Raw messages: {request.messages}")
            for i, msg in enumerate(request.messages):
                logger.info(f"Message {i}: role={msg.role}, content_type={type(msg.content)}, content={msg.content[:100]}...")  # Логируем только первые 100 символов
                content = msg.content
                # Если content уже строка, используем как есть
                if isinstance(content, str):
                    messages.append({"role": msg.role, "content": content})
                # Если это список (для мультимодальных запросов)
                elif isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif isinstance(item, str):
                            text_parts.append(item)
                    content = " ".join(text_parts)
                    messages.append({"role": msg.role, "content": content})
                else:
                    # Для других типов преобразуем в строку
                    messages.append({"role": msg.role, "content": str(content)})
        
        logger.info(f"Processed messages count: {len(messages)}")
        
        # Параметры
        kwargs = {"max_tokens": 1000}
        if request.max_tokens:
            kwargs["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.stream:
            kwargs["stream"] = True
            
        logger.info(f"Calling provider with {len(messages)} messages and kwargs: {kwargs}")
        
        # Вызов провайдера
        response = await asyncio.wait_for(
            provider.chat_completion(messages, **kwargs),
            timeout=120.0  # Увеличиваем таймаут для локальной модели
        )
        
        # Обработка streaming response
        if request.stream:
            logger.info("Streaming response requested")
            
            # Для streaming ответов создаем кастомный обработчик
            from fastapi.responses import StreamingResponse
            import json
            
            async def streaming_generator():
                async for chunk in response:
                    # Преобразуем chunk в JSON-совместимый формат
                    if hasattr(chunk, 'to_dict'):
                        chunk_dict = chunk.to_dict()
                    elif hasattr(chunk, 'dict'):
                        chunk_dict = chunk.dict()
                    else:
                        chunk_dict = {
                            "id": f"chatcmpl-{int(time.time())}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": request.model or current_provider,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "content": getattr(chunk, 'content', '') or getattr(getattr(chunk, 'choices', [{}])[0], 'delta', {}).get('content', '')
                                    },
                                    "finish_reason": getattr(chunk, 'finish_reason', None)
                                }
                            ]
                        }
                    
                    yield f"data: {json.dumps(chunk_dict)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                streaming_generator(),
                media_type="text/event-stream"
            )
        
        logger.info("Response received successfully")
        output_text = response.choices[0].message.content
        
        # Подсчет токенов
        input_tokens = token_counter.count_tokens(str(messages), current_provider)
        output_tokens = token_counter.count_tokens(output_text, current_provider)
        
        # Формирование ответа в формате OpenAI API
        response_data = {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": request.model or current_provider,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": output_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
        }
        
        logger.info(f"Response formatted successfully. Tokens: {input_tokens}+{output_tokens}")
        return response_data
        
    except asyncio.TimeoutError:
        logger.error("Request timeout")
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Добавляем роутер к приложению
from fastapi import APIRouter
v1_router = APIRouter(prefix="/v1")
app.include_router(v1_router)

# Добавляем новые endpoints для тестирования
@app.get("/providers")
async def list_providers():
    """Список доступных провайдеров"""
    return {"providers": list(providers.keys()), "current": current_provider}

@app.post("/switch-provider/{provider_name}")
async def switch_provider(provider_name: str):
    """Переключение провайдера"""
    global current_provider
    if provider_name not in providers:
        raise HTTPException(status_code=400, detail=f"Provider {provider_name} not found")
    current_provider = provider_name
    return {"message": f"Switched to {provider_name}", "provider": current_provider}

# Добавляем обработчик для отлова ошибок валидации Pydantic
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    body = await request.body()
    body_str = body.decode('utf-8', errors='ignore') if body else "empty"
    logger.error(f"❌ Pydantic validation error: {exc}")
    logger.error(f"❌ Request body length: {len(body_str)} characters")
    
    # Логируем первые 500 символов для анализа
    preview_length = min(500, len(body_str))
    logger.error(f"❌ Request body preview: {body_str[:preview_length]}")
    
    logger.error(f"❌ Error details: {exc.errors()}")
    logger.error(f"❌ Error type: {type(exc)}")
    
    # Добавляем дополнительную диагностику
    import json
    try:
        parsed_body = json.loads(body_str) if body_str != "empty" else {}
        logger.error(f"❌ Parsed JSON keys: {list(parsed_body.keys()) if isinstance(parsed_body, dict) else 'Not a dict'}")
        
        # Логируем структуру messages если есть
        if isinstance(parsed_body, dict) and 'messages' in parsed_body:
            messages = parsed_body['messages']
            logger.error(f"❌ Messages count: {len(messages) if isinstance(messages, list) else 'Not a list'}")
            if isinstance(messages, list) and messages:
                first_msg = messages[0]
                logger.error(f"❌ First message keys: {list(first_msg.keys()) if isinstance(first_msg, dict) else 'Not a dict'}")
                if isinstance(first_msg, dict) and 'content' in first_msg:
                    content = first_msg['content']
                    logger.error(f"❌ First message content type: {type(content)}")
                    if isinstance(content, str):
                        logger.error(f"❌ First message content preview: {content[:100]}...")
                
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error: {e}")
    
    return JSONResponse(
        status_code=422,  # Используем 422 как в оригинальном OpenAI API
        content={"detail": exc.errors(), "body_preview": body_str[:500]}
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