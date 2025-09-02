import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import requests
import time
from server import app
import uvicorn
from config import Config

class ProxyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM Proxy")
        self.root.geometry("800x600")

        # Переменные
        self.current_provider = tk.StringVar(value=Config.DEFAULT_PROVIDER)
        self.server_running = False

        # Создание виджетов
        self.create_widgets()

        # Запуск обновления статистики
        self.update_stats()

    def create_widgets(self):
        # Фрейм для выбора провайдера
        provider_frame = ttk.LabelFrame(self.root, text="Выбор провайдера")
        provider_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(provider_frame, text="Провайдер:").grid(row=0, column=0, padx=5, pady=5)
        provider_combo = ttk.Combobox(provider_frame, textvariable=self.current_provider, values=["deepseek", "moonshot"])
        provider_combo.grid(row=0, column=1, padx=5, pady=5)
        provider_combo.bind("<<ComboboxSelected>>", self.change_provider)

        # Кнопка запуска сервера
        self.start_button = ttk.Button(provider_frame, text="Запустить сервер", command=self.start_server)
        self.start_button.grid(row=0, column=2, padx=5, pady=5)

        # Фрейм для статистики
        stats_frame = ttk.LabelFrame(self.root, text="Статистика")
        stats_frame.pack(pady=10, padx=10, fill="x")

        self.total_requests_label = ttk.Label(stats_frame, text="Всего запросов: 0")
        self.total_requests_label.grid(row=0, column=0, padx=5, pady=5)

        self.total_tokens_label = ttk.Label(stats_frame, text="Всего токенов: 0")
        self.total_tokens_label.grid(row=0, column=1, padx=5, pady=5)

        self.total_cost_label = ttk.Label(stats_frame, text="Общая стоимость: $0.00")
        self.total_cost_label.grid(row=0, column=2, padx=5, pady=5)

        # Фрейм для запросов
        requests_frame = ttk.LabelFrame(self.root, text="Последние запросы")
        requests_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.requests_text = scrolledtext.ScrolledText(requests_frame, height=20)
        self.requests_text.pack(fill="both", expand=True)

    def change_provider(self, event):
        provider = self.current_provider.get()
        try:
            response = requests.post("http://localhost:8000/set_provider", json=provider)
            if response.status_code == 200:
                print(f"Провайдер изменен на {provider}")
            else:
                print("Ошибка изменения провайдера")
        except:
            print("Сервер не запущен")

    def start_server(self):
        if not self.server_running:
            self.server_running = True
            self.start_button.config(text="Сервер запущен", state="disabled")
            threading.Thread(target=self.run_server, daemon=True).start()

    def run_server(self):
        uvicorn.run(app, host=Config.SERVER_HOST, port=Config.SERVER_PORT)

    def update_stats(self):
        if self.server_running:
            try:
                response = requests.get("http://localhost:8000/stats")
                if response.status_code == 200:
                    data = response.json()
                    self.total_requests_label.config(text=f"Всего запросов: {data['total_requests']}")
                    self.total_tokens_label.config(text=f"Всего токенов: {data['total_tokens']}")
                    self.total_cost_label.config(text=f"Общая стоимость: ${data['total_cost']:.4f}")

                    # Обновление списка запросов
                    self.requests_text.delete(1.0, tk.END)
                    for req in data['requests'][-10:]:  # Последние 10
                        timestamp = time.strftime("%H:%M:%S", time.localtime(req['timestamp']))
                        self.requests_text.insert(tk.END, f"{timestamp} - {req['provider']} - Токены: {req['input_tokens']}+{req['output_tokens']} - Стоимость: ${req['cost']:.4f}\n")
            except:
                pass

        self.root.after(5000, self.update_stats)  # Обновление каждые 5 секунд

if __name__ == "__main__":
    root = tk.Tk()
    gui = ProxyGUI(root)
    root.mainloop()