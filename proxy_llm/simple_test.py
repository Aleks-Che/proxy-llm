#!/usr/bin/env python3

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    logger.info("🔍 Request received")
    
    # Просто читаем тело запроса и возвращаем тестовый ответ
    body = await request.body()
    body_str = body.decode('utf-8', errors='ignore') if body else "empty"
    logger.info(f"🔍 Request body: {body_str}")
    
    return {
        "id": "test-id",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "test-model",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "This is a test response from simple server"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10006)
