from openai import AsyncOpenAI
import asyncio
import aiohttp
import json
import httpx
import base64
import uuid
import time
from config import config as Config
import logging

logger = logging.getLogger(__name__)

class GigaChatProvider:
    def __init__(self):
        provider_config = Config.get_provider_config("gigachat")
        self.api_key = provider_config.get("api_key", "")
        self.base_url = provider_config.get("base_url", "https://gigachat.devices.sberbank.ru/api/v1")
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        
        # Parse the authorization key (should be in format "client_id:client_secret")
        if self.api_key and ":" in self.api_key:
            self.client_id, self.client_secret = self.api_key.split(":", 1)
            # Create Basic auth header value (without "Basic " prefix)
            auth_string = f"{self.client_id}:{self.client_secret}"
            self.auth_key = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
            logger.info(f"Parsed GigaChat credentials for client: {self.client_id[:8]}...")
        else:
            self.auth_key = self.api_key
            self.client_id = ""
            self.client_secret = ""
            logger.warning("GigaChat API key format should be 'client_id:client_secret'")
        
        # Token management
        self.access_token = None
        self.token_expires_at = 0
        
        # Get model configuration
        models = provider_config.get("models", [])
        self.model = "GigaChat-2-Max"  # Default to the latest model
        for model in models:
            if model["name"] == "GigaChat-2-Max":
                self.model = "GigaChat-2-Max"
                break
            elif model["name"] == "GigaChat-Pro":
                self.model = "GigaChat-Pro"
        
        # Initialize OpenAI client with dynamic token
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize or reinitialize the OpenAI client with current token"""
        if self.access_token:
            self.client = AsyncOpenAI(
                api_key=self.access_token,
                base_url=self.base_url,
                http_client=httpx.AsyncClient(verify=False)
            )
        else:
            self.client = None

    async def _get_access_token(self):
        """Get or refresh access token using OAuth 2.0 flow"""
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Check if current token is still valid (with 5 minute buffer)
        if self.access_token and self.token_expires_at > current_time + 300000:
            return self.access_token
        
        try:
            # Generate unique request ID
            request_id = str(uuid.uuid4())
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "RqUID": request_id,
                    "Authorization": f"Basic {self.auth_key}"
                }
                
                data = {
                    "scope": "GIGACHAT_API_PERS"  # For individual users
                }
                
                logger.info(f"Requesting new access token for GigaChat (RqUID: {request_id})")
                logger.info(f"Auth URL: {self.auth_url}")
                logger.info(f"Authorization header: Basic {self.auth_key[:20]}...")
                
                async with session.post(self.auth_url, headers=headers, data=data) as response:
                    logger.info(f"Token response status: {response.status}")
                    response_text = await response.text()
                    logger.info(f"Token response: {response_text[:200]}...")
                    
                    if response.status == 200:
                        try:
                            token_data = json.loads(response_text)
                            self.access_token = token_data.get("access_token")
                            self.token_expires_at = token_data.get("expires_at", 0)
                            
                            if self.access_token:
                                logger.info("Successfully obtained GigaChat access token")
                                self._initialize_client()  # Reinitialize client with new token
                                return self.access_token
                            else:
                                logger.error("No access token in response")
                                return None
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse token response: {e}")
                            return None
                    else:
                        logger.error(f"Failed to get access token: {response.status} - {response_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting GigaChat access token: {e}")
            return None

    async def get_models(self):
        """Получить список доступных моделей от GigaChat"""
        try:
            token = await self._get_access_token()
            if not token:
                logger.error("No valid access token available")
                return []
            
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {token}"}
                async with session.get(f"{self.base_url}/models", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    else:
                        logger.error(f"Failed to fetch models: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []

    async def chat_completion(self, messages, **kwargs):
        """Выполнить чат-запрос к GigaChat"""
        try:
            # Ensure we have a valid access token
            token = await self._get_access_token()
            if not token or not self.client:
                raise Exception("No valid access token available for GigaChat")
            
            # Поддерживаемые параметры для GigaChat
            supported_params = [
                'temperature', 'max_tokens', 'stream', 'top_p', 'frequency_penalty',
                'presence_penalty', 'stop', 'n', 'repetition_penalty', 'update_interval'
            ]
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in supported_params and v is not None}

            logger.info(f"Calling GigaChat with model: {self.model}")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **filtered_kwargs
            )
            return response
            
        except Exception as e:
            logger.error(f"GigaChat chat completion error: {e}")
            # Try to refresh token and retry once
            if "401" in str(e) or "Unauthorized" in str(e):
                logger.info("Attempting to refresh token and retry...")
                self.access_token = None  # Clear invalid token
                token = await self._get_access_token()
                if token and self.client:
                    try:
                        response = await self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            **filtered_kwargs
                        )
                        return response
                    except Exception as retry_error:
                        logger.error(f"Retry after token refresh failed: {retry_error}")
                        raise
            raise