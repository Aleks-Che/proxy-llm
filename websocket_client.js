/**
 * WebSocket Client для roocode/cline расширений
 * Создает постоянное соединение для обхода сетевых ограничений
 */

class PersistentProxyClient {
  constructor(wsUrl = "ws://localhost:8765", options = {}) {
    this.wsUrl = wsUrl;
    this.options = {
      reconnectInterval: options.reconnectInterval || 5000,
      maxReconnectAttempts: options.maxReconnectAttempts || 10,
      connectionTimeout: options.connectionTimeout || 30000,
      heartbeatInterval: options.heartbeatInterval || 15000,
      ...options,
    };

    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.messageQueue = [];
    this.pendingRequests = new Map();
    this.requestId = 0;
    this.heartbeatInterval = null;

    // Callbacks
    this.onConnect = options.onConnect || (() => {});
    this.onDisconnect = options.onDisconnect || (() => {});
    this.onError = options.onError || (() => {});
    this.onMessage = options.onMessage || (() => {});
  }

  /**
   * Подключение к WebSocket серверу
   */
  connect() {
    if (this.isConnected) {
      console.log("Уже подключены к WebSocket серверу");
      return;
    }

    try {
      console.log(`Подключение к WebSocket: ${this.wsUrl}`);
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => this.handleOpen();
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onclose = () => this.handleClose();
      this.ws.onerror = (error) => this.handleError(error);
    } catch (error) {
      console.error("Ошибка при создании WebSocket:", error);
      this.scheduleReconnect();
    }
  }

  /**
   * Обработка открытия соединения
   */
  handleOpen() {
    console.log("WebSocket соединение установлено");
    this.isConnected = true;
    this.reconnectAttempts = 0;

    // Запускаем heartbeat
    this.startHeartbeat();

    // Отправляем накопленные сообщения
    this.flushMessageQueue();

    // Вызываем callback
    this.onConnect();
  }

  /**
   * Обработка входящих сообщений
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      console.log("Получено сообщение от сервера:", data);

      // Проверяем, это ответ на запрос или служебное сообщение
      if (data.requestId && this.pendingRequests.has(data.requestId)) {
        // Ответ на запрос
        const { resolve, reject } = this.pendingRequests.get(data.requestId);
        this.pendingRequests.delete(data.requestId);

        if (data.error) {
          reject(new Error(data.error));
        } else {
          resolve(data);
        }
      } else {
        // Служебное сообщение или широковещательное
        this.onMessage(data);
      }
    } catch (error) {
      console.error("Ошибка при обработке сообщения:", error);
      this.onError(error);
    }
  }

  /**
   * Обработка закрытия соединения
   */
  handleClose() {
    console.log("WebSocket соединение закрыто");
    this.isConnected = false;
    this.stopHeartbeat();

    // Вызываем callback
    this.onDisconnect();

    // Планируем переподключение
    this.scheduleReconnect();
  }

  /**
   * Обработка ошибок
   */
  handleError(error) {
    console.error("WebSocket ошибка:", error);
    this.onError(error);
  }

  /**
   * Запуск heartbeat для поддержания соединения
   */
  startHeartbeat() {
    this.stopHeartbeat();

    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
        this.send({ type: "ping", timestamp: Date.now() });
      }
    }, this.options.heartbeatInterval);
  }

  /**
   * Остановка heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Планирование переподключения
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.error(
        "Достигнуто максимальное количество попыток переподключения"
      );
      return;
    }

    this.reconnectAttempts++;
    console.log(
      `Переподключение через ${this.options.reconnectInterval}ms (попытка ${this.reconnectAttempts})`
    );

    setTimeout(() => {
      this.connect();
    }, this.options.reconnectInterval);
  }

  /**
   * Отправка сообщения
   */
  send(data) {
    if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
      try {
        const message = JSON.stringify(data);
        this.ws.send(message);
        console.log("Сообщение отправлено:", data);
        return true;
      } catch (error) {
        console.error("Ошибка при отправке сообщения:", error);
        return false;
      }
    } else {
      console.warn("Соединение не активно, сообщение добавлено в очередь");
      this.messageQueue.push(data);
      return false;
    }
  }

  /**
   * Отправка запроса с ожиданием ответа
   */
  async sendRequest(requestData) {
    return new Promise((resolve, reject) => {
      const requestId = ++this.requestId;
      const request = {
        ...requestData,
        requestId: requestId,
        timestamp: Date.now(),
      };

      // Сохраняем promise для ответа
      this.pendingRequests.set(requestId, { resolve, reject });

      // Отправляем запрос
      if (!this.send(request)) {
        // Если не удалось отправить, отклоняем promise
        this.pendingRequests.delete(requestId);
        reject(new Error("Не удалось отправить запрос"));
      }

      // Таймаут на ответ
      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error("Таймаут запроса"));
        }
      }, this.options.connectionTimeout);
    });
  }

  /**
   * Отправка запроса в формате OpenAI API
   */
  async sendChatCompletion(messages, model = "gpt-4", options = {}) {
    const requestData = {
      model: model,
      messages: messages,
      stream: options.stream || false,
      max_tokens: options.max_tokens || 1000,
      temperature: options.temperature || 0.7,
      ...options,
    };

    return await this.sendRequest(requestData);
  }

  /**
   * Отправка накопленных сообщений из очереди
   */
  flushMessageQueue() {
    console.log(`Отправка ${this.messageQueue.length} накопленных сообщений`);

    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  /**
   * Отключение от сервера
   */
  disconnect() {
    console.log("Отключение от WebSocket сервера");

    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.isConnected = false;
    this.reconnectAttempts = this.options.maxReconnectAttempts; // Предотвращаем автопереподключение
  }

  /**
   * Получение статуса соединения
   */
  getStatus() {
    return {
      connected: this.isConnected,
      url: this.wsUrl,
      reconnectAttempts: this.reconnectAttempts,
      pendingRequests: this.pendingRequests.size,
      queueSize: this.messageQueue.length,
    };
  }
}

// Пример использования в расширении roocode/cline
class OpenAICompatibleClient {
  constructor(wsUrl = "ws://localhost:8765", apiKey = "dummy") {
    this.wsClient = new PersistentProxyClient(wsUrl, {
      onConnect: () => console.log("Подключено к прокси"),
      onDisconnect: () => console.log("Отключено от прокси"),
      onError: (error) => console.error("Ошибка прокси:", error),
      onMessage: (data) => console.log("Сообщение от прокси:", data),
    });

    this.apiKey = apiKey;
  }

  /**
   * Инициализация клиента
   */
  async initialize() {
    this.wsClient.connect();

    // Ждем подключения
    while (!this.wsClient.isConnected) {
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
  }

  /**
   * Отправка запроса на чат-комплишн
   */
  async chatCompletion(messages, model = "gpt-4", options = {}) {
    try {
      const response = await this.wsClient.sendChatCompletion(
        messages,
        model,
        options
      );
      return response;
    } catch (error) {
      console.error("Ошибка chat completion:", error);
      throw error;
    }
  }

  /**
   * Потоковая передача ответа
   */
  async *streamChatCompletion(messages, model = "gpt-4", options = {}) {
    // Для потоковой передачи используем обычный запрос и разбиваем на части
    const response = await this.chatCompletion(messages, model, {
      ...options,
      stream: true,
    });

    // Эмулируем streaming, разбивая ответ на части
    const content = response.choices[0]?.message?.content || "";
    const words = content.split(" ");

    for (let i = 0; i < words.length; i++) {
      yield {
        id: response.id,
        object: "chat.completion.chunk",
        created: response.created,
        model: response.model,
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

      // Небольшая задержка для эмуляции потоковой передачи
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
  }

  /**
   * Закрытие соединения
   */
  close() {
    this.wsClient.disconnect();
  }
}

// Экспорт для использования в других модулях
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    PersistentProxyClient,
    OpenAICompatibleClient,
  };
}
