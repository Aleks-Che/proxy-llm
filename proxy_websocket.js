const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");
const cors = require("cors");
const WebSocket = require("ws");
const http = require("http");

const app = express();

// Отключает проверку SSL-сертификатов (небезопасно, использовать только для разработки)
process.env["NODE_TLS_REJECT_UNAUTHORIZED"] = 0;

// Настройка CORS
app.use(
  cors({
    exposedHeaders: "*",
  })
);

// WebSocket клиент для подключения к WebSocket Bridge
class WebSocketBridgeClient {
  constructor(wsUrl = "ws://localhost:8765") {
    this.wsUrl = wsUrl;
    this.ws = null;
    this.isConnected = false;
    this.messageQueue = [];
    this.pendingRequests = new Map();
    this.requestId = 0;
    this.reconnectInterval = 5000;
    this.maxReconnectAttempts = 10;
    this.reconnectAttempts = 0;
  }

  connect() {
    if (this.isConnected) {
      console.log("WebSocket уже подключен");
      return;
    }

    try {
      console.log(`Подключение к WebSocket Bridge: ${this.wsUrl}`);
      this.ws = new WebSocket(this.wsUrl);

      this.ws.on("open", () => {
        console.log("WebSocket соединение установлено");
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.flushMessageQueue();
      });

      this.ws.on("message", (data) => {
        try {
          const response = JSON.parse(data);
          console.log(
            "Получен ответ от WebSocket Bridge:",
            response.id || "no id"
          );

          if (
            response.requestId &&
            this.pendingRequests.has(response.requestId)
          ) {
            const { resolve, reject } = this.pendingRequests.get(
              response.requestId
            );
            this.pendingRequests.delete(response.requestId);

            if (response.error) {
              reject(new Error(response.error));
            } else {
              resolve(response);
            }
          }
        } catch (error) {
          console.error("Ошибка при обработке сообщения:", error);
        }
      });

      this.ws.on("close", () => {
        console.log("WebSocket соединение закрыто");
        this.isConnected = false;
        this.scheduleReconnect();
      });

      this.ws.on("error", (error) => {
        console.error("WebSocket ошибка:", error);
        this.isConnected = false;
      });
    } catch (error) {
      console.error("Ошибка при создании WebSocket:", error);
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(
        "Достигнуто максимальное количество попыток переподключения"
      );
      return;
    }

    this.reconnectAttempts++;
    console.log(
      `Переподключение через ${this.reconnectInterval}ms (попытка ${this.reconnectAttempts})`
    );

    setTimeout(() => {
      this.connect();
    }, this.reconnectInterval);
  }

  async sendRequest(requestData) {
    return new Promise((resolve, reject) => {
      const requestId = ++this.requestId;
      const request = {
        ...requestData,
        requestId: requestId,
        timestamp: Date.now(),
      };

      this.pendingRequests.set(requestId, { resolve, reject });

      if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify(request));
          console.log("Запрос отправлен в WebSocket Bridge:", requestId);
        } catch (error) {
          console.error("Ошибка при отправке запроса:", error);
          this.pendingRequests.delete(requestId);
          reject(error);
        }
      } else {
        console.log("Соединение не активно, запрос добавлен в очередь");
        this.messageQueue.push(request);
        reject(new Error("WebSocket не подключен"));
      }
    });
  }

  flushMessageQueue() {
    console.log(`Отправка ${this.messageQueue.length} накопленных сообщений`);

    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message));
      }
    }
  }

  isReady() {
    return this.isConnected && this.ws.readyState === WebSocket.OPEN;
  }
}

// Создаем экземпляр WebSocket клиента
const wsClient = new WebSocketBridgeClient("ws://localhost:8765");

// Подключаемся к WebSocket Bridge
wsClient.connect();

// Middleware для обработки OpenAI API запросов
const openaiProxy = async (req, res) => {
  try {
    console.log("Получен OpenAI API запрос:", req.method, req.url);
    console.log("Заголовки:", req.headers);

    // Собираем тело запроса
    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
    });

    req.on("end", async () => {
      try {
        const requestData = JSON.parse(body);
        console.log("Тело запроса:", JSON.stringify(requestData, null, 2));

        // Проверяем, готов ли WebSocket
        if (!wsClient.isReady()) {
          console.error("WebSocket не готов, возвращаем ошибку");
          return res.status(503).json({
            error: {
              message: "WebSocket Bridge не подключен",
              type: "connection_error",
              code: "websocket_unavailable",
            },
          });
        }

        // Отправляем запрос через WebSocket
        console.log("Отправка запроса через WebSocket Bridge...");
        const response = await wsClient.sendRequest(requestData);

        console.log("Получен ответ от WebSocket Bridge");

        // Формируем ответ в формате OpenAI API
        const openaiResponse = {
          id: response.id || `chatcmpl-${Date.now()}`,
          object: "chat.completion",
          created: response.created || Math.floor(Date.now() / 1000),
          model: response.model || requestData.model || "gpt-4",
          choices: response.choices || [
            {
              index: 0,
              message: {
                role: "assistant",
                content:
                  response.choices?.[0]?.message?.content ||
                  "Ответ получен через WebSocket Bridge",
              },
              finish_reason: "stop",
            },
          ],
          usage: response.usage || {
            prompt_tokens: 0,
            completion_tokens: 0,
            total_tokens: 0,
          },
        };

        res.json(openaiResponse);
      } catch (error) {
        console.error("Ошибка при обработке запроса:", error);
        res.status(500).json({
          error: {
            message: error.message,
            type: "internal_error",
            code: "internal_error",
          },
        });
      }
    });
  } catch (error) {
    console.error("Ошибка в openaiProxy:", error);
    res.status(500).json({
      error: {
        message: error.message,
        type: "internal_error",
        code: "internal_error",
      },
    });
  }
};

// Middleware для streaming ответов
const streamingProxy = async (req, res) => {
  try {
    console.log("Получен streaming запрос:", req.method, req.url);

    // Устанавливаем заголовки для streaming
    res.writeHead(200, {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    });

    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
    });

    req.on("end", async () => {
      try {
        const requestData = JSON.parse(body);
        console.log("Streaming запрос:", JSON.stringify(requestData, null, 2));

        if (!wsClient.isReady()) {
          res.write(`data: {"error": "WebSocket Bridge не подключен"}\n\n`);
          res.end();
          return;
        }

        // Для streaming эмулируем потоковый ответ
        const response = await wsClient.sendRequest(requestData);

        // Отправляем ответ по частям
        const content = response.choices?.[0]?.message?.content || "";
        const words = content.split(" ");

        for (let i = 0; i < words.length; i++) {
          const chunk = {
            id: response.id || `chatcmpl-${Date.now()}`,
            object: "chat.completion.chunk",
            created: response.created || Math.floor(Date.now() / 1000),
            model: response.model || requestData.model || "gpt-4",
            choices: [
              {
                index: 0,
                delta: {
                  content: (i === 0 ? "" : " ") + words[i],
                },
                finish_reason: i === words.length - 1 ? "stop" : null,
              },
            ],
          };

          res.write(`data: ${JSON.stringify(chunk)}\n\n`);

          // Небольшая задержка для эмуляции потоковой передачи
          await new Promise((resolve) => setTimeout(resolve, 50));
        }

        // Финальный chunk
        const finalChunk = {
          id: response.id || `chatcmpl-${Date.now()}`,
          object: "chat.completion.chunk",
          created: response.created || Math.floor(Date.now() / 1000),
          model: response.model || requestData.model || "gpt-4",
          choices: [
            {
              index: 0,
              delta: {},
              finish_reason: "stop",
            },
          ],
        };

        res.write(`data: ${JSON.stringify(finalChunk)}\n\n`);
        res.write("data: [DONE]\n\n");
        res.end();
      } catch (error) {
        console.error("Ошибка при streaming:", error);
        res.write(`data: {"error": "${error.message}"}\n\n`);
        res.end();
      }
    });
  } catch (error) {
    console.error("Ошибка в streamingProxy:", error);
    res.write(`data: {"error": "${error.message}"}\n\n`);
    res.end();
  }
};

// Прокси для OpenAI API через WebSocket
app.use("/v1/chat/completions", (req, res) => {
  if (
    req.headers.accept?.includes("text/event-stream") ||
    req.query.stream === "true"
  ) {
    return streamingProxy(req, res);
  } else {
    return openaiProxy(req, res);
  }
});

// Прокси для других OpenAI endpoints
app.use("/v1/*", (req, res) => {
  // Для других endpoints пока возвращаем заглушку
  res.json({
    object: "list",
    data: [],
  });
});

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    websocket_connected: wsClient.isReady(),
    timestamp: new Date().toISOString(),
  });
});

// Статистика
app.get("/stats", (req, res) => {
  res.json({
    websocket_connected: wsClient.isReady(),
    pending_requests: wsClient.pendingRequests.size,
    queue_size: wsClient.messageQueue.length,
    reconnect_attempts: wsClient.reconnectAttempts,
  });
});

// Существующие прокси маршруты (оставляем для обратной совместимости)
// Прокси для маршрута /ckr.cab/*
app.use(
  "/ckr.cab/*",
  createProxyMiddleware({
    target: "http://127.0.0.1:4000",
    secure: false,
    changeOrigin: true,
    onProxyReq: function (proxyReq, req, res) {
      proxyReq.setHeader("authorization", "123");
      proxyReq.setHeader("iv-user", "iv");
      proxyReq.setHeader("X-Real-Ip", "ip");
      proxyReq.setHeader("x-authorities", "com_ckr_non_any");
    },
  })
);

// Прокси для маршрута /ckr.game/*
app.use(
  "/ckr.game/*",
  createProxyMiddleware({
    target: "http://127.0.0.1:4005",
    secure: false,
    changeOrigin: true,
    onProxyReq: function (proxyReq, req, res) {
      proxyReq.setHeader("authorization", "123");
      proxyReq.setHeader("iv-user", "iv");
      proxyReq.setHeader("X-Real-Ip", "ip");
      proxyReq.setHeader("x-authorities", "com_ckr_non_any");
    },
  })
);

// Прокси для маршрута /ckr.sales/*
app.use(
  "/ckr.sales/*",
  createProxyMiddleware({
    target: "http://127.0.0.1:4010",
    secure: false,
    changeOrigin: true,
    onProxyReq: function (proxyReq, req, res) {
      proxyReq.setHeader("authorization", "123");
      proxyReq.setHeader("iv-user", "iv");
      proxyReq.setHeader("X-Real-Ip", "ip");
      proxyReq.setHeader("x-authorities", "com_ckr_non_any");
    },
  })
);

// Запуск сервера на порту 8000
const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {
  console.log(`WebSocket Proxy server is running on port ${PORT}`);
  console.log(`WebSocket Bridge connection: ${wsClient.wsUrl}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(
    `OpenAI API endpoint: http://localhost:${PORT}/v1/chat/completions`
  );
});

// Graceful shutdown
process.on("SIGINT", () => {
  console.log("\nПолучен сигнал SIGINT, закрытие соединений...");
  if (wsClient.ws) {
    wsClient.ws.close();
  }
  process.exit(0);
});

process.on("SIGTERM", () => {
  console.log("\nПолучен сигнал SIGTERM, закрытие соединений...");
  if (wsClient.ws) {
    wsClient.ws.close();
  }
  process.exit(0);
});
