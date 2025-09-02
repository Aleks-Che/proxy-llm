
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
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
    content: Union[str, List[Dict[str, Any]], Dict[str, Any]]  # Поддержка всех типов content
    
    class Config:
        extra = "allow"  # Разрешить дополнительные поля

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    reasoning_effort: Optional[str] = None
    stream_options: Optional[Dict[str, Any]] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    suffix: Optional[str] = None
    echo: Optional[bool] = None
    best_of: Optional[int] = None
    logprobs: Optional[int] = None
    n: Optional[int] = None
    stop: Optional[List[str]] = None
    
    # Специфичные поля от Cline
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    response_format: Optional[Dict[str, Any]] = None
    seed: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    truncation_strategy: Optional[Dict[str, Any]] = None
    reasoning: Optional[Dict[str, Any]] = None
    parallel_tool_calls: Optional[bool] = None
    store: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Разрешаем любые дополнительные поля от Cline
    class Config:
        extra = "allow"

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
        
        # Обработка сообщений - более гибкая
        messages = []
        if request.messages:
            logger.info(f"Raw messages: {request.messages}")
            for i, msg in enumerate(request.messages):
                logger.info(f"Message {i}: role={msg.role}, content_type={type(msg.content)}")
                
                # Обрабатываем content в зависимости от типа
                content = msg.content
                
                # Если content - строка
                if isinstance(content, str):
                    processed_content = content
                # Если content - список (мультимодальные данные)
                elif isinstance(content, list):
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                            # Игнорируем image_url и другие типы для простоты
                        elif isinstance(item, str):
                            text_parts.append(item)
                    processed_content = " ".join(text_parts)
                # Если content - dict
                elif isinstance(content, dict):
                    processed_content = str(content)  # Или извлечь текст из dict
                # Для других типов
                else:
                    processed_content = str(content)
                
                messages.append({
                    "role": msg.role,
                    "content": processed_content
                })
                
                logger.info(f"Processed message {i}: {processed_content[:100]}...")
        
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
            logger.info(f"Stream options: {request.stream_options}")
            logger.info(f"Reasoning effort: {request.reasoning_effort}")
            
            # Для streaming ответов создаем кастомный обработчик
            from fastapi.responses import StreamingResponse
            import json
            
            async def streaming_generator():
                # Подсчет токенов для usage статистики
                input_tokens = token_counter.count_tokens(str(messages), current_provider)
                completion_tokens = 0
                accumulated_content = ""
                
                async for chunk in response:
                    # Извлекаем контент из чанка для подсчета токенов
                    content = ""
                    if hasattr(chunk, 'content'):
                        content = getattr(chunk, 'content', '')
                    elif hasattr(chunk, 'choices') and getattr(chunk, 'choices'):
                        choices = getattr(chunk, 'choices')
                        if choices and hasattr(choices[0], 'delta'):
                            delta = getattr(choices[0], 'delta')
                            if hasattr(delta, 'content'):
                                content = getattr(delta, 'content', '')
                    
                    # Обновляем accumulated_content и completion_tokens
                    if content:
                        accumulated_content += content
                        completion_tokens = token_counter.count_tokens(accumulated_content, current_provider)
                    
                    # Преобразуем chunk в JSON-совместимый формат
                    if hasattr(chunk, 'model_dump'):
                        chunk_dict = chunk.model_dump()
                    elif hasattr(chunk, 'to_dict'):
                        chunk_dict = chunk.to_dict()
                    elif hasattr(chunk, 'dict'):
                        chunk_dict = chunk.dict()
                    else:
                        # Форматируем ответ в соответствии с форматом Cline
                        chunk_dict = {
                            "id": f"chatcmpl-{int(time.time())}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": request.model or current_provider,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "content": content,
                                        "reasoning_content": None  # Для совместимости с Cline
                                    },
                                    "finish_reason": getattr(chunk, 'finish_reason', None)
                                }
                            ]
                        }
                    
                    # Обновляем completion_tokens во всех чанках
                    if request.stream_options and request.stream_options.get("include_usage", False):
                        chunk_dict["usage"] = {
                            "prompt_tokens": input_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": input_tokens + completion_tokens,
                            "prompt_tokens_details": {
                                "cached_tokens": 0  # Пока не поддерживаем кэширование
                            },
                            "prompt_cache_miss_tokens": input_tokens
                        }
                    
                    # Убеждаемся, что JSON корректен
                    try:
                        json_str = json.dumps(chunk_dict, ensure_ascii=False)
                        yield f"data: {json_str}\n\n"
                    except Exception as e:
                        logger.error(f"JSON serialization error: {e}")
                        yield f"data: {{\"error\": \"JSON serialization failed\"}}\n\n"
                
                # Финальный chunk с полной статистикой usage
                if request.stream_options and request.stream_options.get("include_usage", False):
                    final_chunk = {
                        "id": f"chatcmpl-{int(time.time())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": request.model or current_provider,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": input_tokens,
                            "completion_tokens": completion_tokens,
                            "total_tokens": input_tokens + completion_tokens,
                            "prompt_tokens_details": {
                                "cached_tokens": 0
                            },
                            "prompt_cache_miss_tokens": input_tokens
                        }
                    }
                    try:
                        json_str = json.dumps(final_chunk, ensure_ascii=False)
                        yield f"data: {json_str}\n\n"
                    except Exception as e:
                        logger.error(f"Final chunk JSON error: {e}")
                
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

@app.post("/debug/cline")
async def debug_cline_request(request: Request):
    """Эндпоинт для отладки запросов от Cline"""
    body = await request.body()
    body_str = body.decode('utf-8', errors='ignore')
    
    try:
        import json
        parsed = json.loads(body_str)
    except:
        parsed = {"error": "Invalid JSON"}
    
    return {
        "headers": dict(request.headers),
        "body": parsed,
        "raw_body": body_str,
        "method": request.method,
        "url": str(request.url)
    }

# Добавляем обработчик для отлова ошибок валидации Pydantic
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    body = await request.body()
    body_str = body.decode('utf-8', errors='ignore') if body else "empty"
    
    logger.error("=== PYDANTIC VALIDATION ERROR ===")
    logger.error(f"Request body length: {len(body_str)}")
    logger.error(f"Request body preview: {body_str[:1000]}")
    logger.error(f"Validation errors: {exc.errors()}")
    
    # Пытаемся распарсить JSON для анализа
    try:
        import json
        parsed = json.loads(body_str)
        logger.error(f"Parsed JSON keys: {list(parsed.keys())}")
        
        # Анализируем messages
        if 'messages' in parsed:
            messages = parsed['messages']
            logger.error(f"Messages count: {len(messages)}")
            if messages:
                first_msg = messages[0]
                logger.error(f"First message keys: {list(first_msg.keys())}")
                if 'content' in first_msg:
                    content = first_msg['content']
                    logger.error(f"Content type: {type(content)}")
                    if isinstance(content, str):
                        logger.error(f"Content preview: {content[:200]}")
        
        # Логируем все неизвестные поля
        known_fields = {
            'model', 'messages', 'temperature', 'max_tokens', 'stream',
            'reasoning_effort', 'stream_options', 'top_p', 'presence_penalty',
            'frequency_penalty', 'logit_bias', 'user', 'suffix', 'echo',
            'best_of', 'logprobs', 'n', 'stop', 'tools', 'tool_choice',
            'response_format', 'seed', 'max_completion_tokens', 'truncation_strategy',
            'reasoning', 'parallel_tool_calls', 'store', 'metadata'
        }
        unknown_fields = set(parsed.keys()) - known_fields
        if unknown_fields:
            logger.error(f"Unknown fields from Cline: {unknown_fields}")
            
    except Exception as e:
        logger.error(f"Error parsing request body: {e}")
    
    # Вместо 422 возвращаем 200 с диагностикой (для отладки)
    return JSONResponse(
        status_code=200,
        content={
            "error": "Validation failed - check logs",
            "cline_request": body_str[:500],
            "validation_errors": exc.errors()
        }
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