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
        self.root.geometry("1000x800")  # Увеличиваем размер окна

        # Переменные
        self.current_provider = tk.StringVar(value=Config.DEFAULT_PROVIDER)
        self.server_running = False
        self.server_process = None
        self.stop_server_flag = False

        # Создание виджетов
        self.create_widgets()

        # Запуск обновления статистики
        self.update_stats()
        
        # Флаг для остановки обновления логов
        self.stop_log_updates = False
        self.log_update_thread = None

        # Обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Фрейм для выбора провайдера
        provider_frame = ttk.LabelFrame(self.root, text="Выбор провайдера")
        provider_frame.pack(pady=10, padx=10, fill="x")

        ttk.Label(provider_frame, text="Провайдер:").grid(row=0, column=0, padx=5, pady=5)
        provider_combo = ttk.Combobox(provider_frame, textvariable=self.current_provider, values=["deepseek", "moonshot", "local"])
        provider_combo.grid(row=0, column=1, padx=5, pady=5)
        provider_combo.bind("<<ComboboxSelected>>", self.change_provider)

        # Кнопка запуска/остановки сервера с иконкой
        self.start_button = ttk.Button(provider_frame, text="▶ Запустить", command=self.toggle_server, width=15)
        self.start_button.grid(row=0, column=2, padx=5, pady=5)

        # Лейбл для отображения порта
        self.port_label = ttk.Label(provider_frame, text=f"Порт: {Config.SERVER_PORT}")
        self.port_label.grid(row=0, column=3, padx=5, pady=5)

        # Фрейм для статистики
        stats_frame = ttk.LabelFrame(self.root, text="Статистика")
        stats_frame.pack(pady=10, padx=10, fill="x")

        self.total_requests_label = ttk.Label(stats_frame, text="Всего запросов: 0")
        self.total_requests_label.grid(row=0, column=0, padx=5, pady=5)

        self.total_tokens_label = ttk.Label(stats_frame, text="Всего токенов: 0")
        self.total_tokens_label.grid(row=0, column=1, padx=5, pady=5)

        self.total_cost_label = ttk.Label(stats_frame, text="Общая стоимость: $0.00")
        self.total_cost_label.grid(row=0, column=2, padx=5, pady=5)

        # Фрейм для логов
        logs_frame = ttk.LabelFrame(self.root, text="Логи запросов и ответов")
        logs_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Создаем notebook для вкладок
        self.notebook = ttk.Notebook(logs_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Вкладка запросов
        requests_frame = ttk.Frame(self.notebook)
        self.notebook.add(requests_frame, text="Запросы пользователя")
        
        self.requests_text = scrolledtext.ScrolledText(requests_frame, height=8, wrap=tk.WORD)
        self.requests_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.requests_text.config(state=tk.DISABLED)

        # Вкладка ответов
        responses_frame = ttk.Frame(self.notebook)
        self.notebook.add(responses_frame, text="Ответы LLM")
        
        self.responses_text = scrolledtext.ScrolledText(responses_frame, height=8, wrap=tk.WORD)
        self.responses_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.responses_text.config(state=tk.DISABLED)

        # Вкладка всех логов
        all_logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(all_logs_frame, text="Все логи")
        
        self.all_logs_text = scrolledtext.ScrolledText(all_logs_frame, height=8, wrap=tk.WORD)
        self.all_logs_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.all_logs_text.config(state=tk.DISABLED)

    def change_provider(self, event):
        provider = self.current_provider.get()
        try:
            response = requests.post(f"http://localhost:{Config.SERVER_PORT}/switch-provider/{provider}")
            if response.status_code == 200:
                print(f"Провайдер изменен на {provider}")
            else:
                print("Ошибка изменения провайдера")
        except:
            print("Сервер не запущен")

    def toggle_server(self):
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        if not self.server_running:
            self.server_running = True
            self.stop_server_flag = False
            self.start_button.config(text="⏹ Остановить", state="normal")
            threading.Thread(target=self.run_server, daemon=True).start()

    def stop_server(self):
        if self.server_running:
            self.server_running = False
            self.stop_server_flag = True
            self.start_button.config(text="▶ Запустить", state="normal")

            # Останавливаем процесс
            if self.server_process and self.server_process.poll() is None:
                try:
                    self.server_process.terminate()
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()
                except Exception as e:
                    print(f"Ошибка при остановке сервера: {e}")

    def run_server(self):
        import subprocess
        import sys
        import os

        try:
            # Запускаем сервер в отдельном процессе
            cmd = [sys.executable, "-c", f"""
import sys
sys.path.insert(0, r"{os.getcwd()}")
import uvicorn
from server import app
from config import Config
uvicorn.run(app, host="{Config.SERVER_HOST}", port={Config.SERVER_PORT})
"""]

            self.server_process = subprocess.Popen(cmd, cwd=os.getcwd())

            # Ждем пока процесс работает
            while not self.stop_server_flag and self.server_process.poll() is None:
                import time
                time.sleep(0.1)

            # Останавливаем процесс если он еще работает
            if self.server_process and self.server_process.poll() is None:
                self.server_process.terminate()
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.server_process.kill()

        except Exception as e:
            if not self.stop_server_flag:
                print(f"Ошибка запуска сервера: {e}")
            self.server_running = False
            self.root.after(0, lambda: self.start_button.config(text="▶ Запустить", state="normal"))

    def update_stats(self):
        if self.server_running and self.server_process and self.server_process.poll() is None:
            try:
                response = requests.get(f"http://localhost:{Config.SERVER_PORT}/stats", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    self.total_requests_label.config(text=f"Всего запросов: {data['total_requests']}")
                    self.total_tokens_label.config(text=f"Всего токенов: {data['total_tokens']}")
                    self.total_cost_label.config(text=f"Общая стоимость: ${data['total_cost']:.6f}")
            except:
                pass
        else:
            # Если сервер не запущен или процесс умер, сбрасываем состояние
            if self.server_running:
                self.stop_server()

        # Запускаем обновление логов в отдельном потоке, если не запущено
        if self.server_running and (self.log_update_thread is None or not self.log_update_thread.is_alive()):
            self.start_log_updates()

        self.root.after(3000, self.update_stats)  # Обновление каждые 3 секунды

    def start_log_updates(self):
        """Запуск обновления логов в отдельном потоке"""
        if self.log_update_thread is not None and self.log_update_thread.is_alive():
            return
            
        self.stop_log_updates = False
        self.log_update_thread = threading.Thread(target=self.log_update_worker, daemon=True)
        self.log_update_thread.start()

    def stop_log_updates(self):
        """Остановка обновления логов"""
        self.stop_log_updates = True
        if hasattr(self, 'log_update_thread'):
            self.log_update_thread.join(timeout=1.0)

    def log_update_worker(self):
        """Рабочий поток для обновления логов"""
        while not self.stop_log_updates and self.server_running:
            try:
                self.update_logs()
                time.sleep(1)  # Обновление каждую секунду
            except Exception as e:
                print(f"Ошибка в потоке обновления логов: {e}")
                time.sleep(2)

    def update_logs(self):
        """Обновление логов запросов и ответов"""
        if not self.server_running:
            return
            
        try:
            # Получаем логи запросов
            response = requests.get(f"http://localhost:{Config.SERVER_PORT}/logs/requests", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"Получено запросов: {len(data['request_logs'])}")
                # Обновляем в основном потоке GUI
                self.root.after(0, lambda: self.update_requests_text(data['request_logs']))

            # Получаем логи ответов
            response = requests.get(f"http://localhost:{Config.SERVER_PORT}/logs/responses", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"Получено ответов: {len(data['response_logs'])}")
                self.root.after(0, lambda: self.update_responses_text(data['response_logs']))

            # Получаем все логи
            response = requests.get(f"http://localhost:{Config.SERVER_PORT}/logs/all", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"Всего логов: {len(data['logs'])}")
                self.root.after(0, lambda: self.update_all_logs_text(data['logs']))

        except Exception as e:
            print(f"Ошибка обновления логов: {e}")

    def update_requests_text(self, logs):
        """Обновление текста запросов в GUI потоке"""
        self.requests_text.config(state=tk.NORMAL)
        self.requests_text.delete(1.0, tk.END)
        
        for log in reversed(logs):  # Новые сверху
            timestamp = time.strftime("%H:%M:%S", time.localtime(log['timestamp']))
            self.requests_text.insert(tk.END, f"[{timestamp}] {log['provider']}:\n")
            self.requests_text.insert(tk.END, f"Запрос: {log['user_message']}\n")
            self.requests_text.insert(tk.END, f"Сообщений: {log['messages_count']}, Stream: {log['stream']}\n")
            self.requests_text.insert(tk.END, "-" * 50 + "\n")
        
        self.requests_text.config(state=tk.DISABLED)

    def update_responses_text(self, logs):
        """Обновление текста ответов в GUI потоке"""
        self.responses_text.config(state=tk.NORMAL)
        self.responses_text.delete(1.0, tk.END)
        
        for log in reversed(logs):  # Новые сверху
            timestamp = time.strftime("%H:%M:%S", time.localtime(log['timestamp']))
            self.responses_text.insert(tk.END, f"[{timestamp}] {log['provider']}:\n")
            self.responses_text.insert(tk.END, f"Ответ: {log['response']}\n")
            self.responses_text.insert(tk.END, f"Токены: {log['input_tokens']}+{log['output_tokens']}\n")
            self.responses_text.insert(tk.END, "-" * 50 + "\n")
        
        self.responses_text.config(state=tk.DISABLED)

    def update_all_logs_text(self, logs):
        """Обновление всех логов в GUI потоке"""
        self.all_logs_text.config(state=tk.NORMAL)
        self.all_logs_text.delete(1.0, tk.END)
        
        for log in logs:  # Уже отсортированы по времени
            timestamp = time.strftime("%H:%M:%S", time.localtime(log['timestamp']))
            if log['type'] == 'request':
                self.all_logs_text.insert(tk.END, f"[{timestamp}] ЗАПРОС {log['provider']}:\n")
                self.all_logs_text.insert(tk.END, f"📤 {log['user_message']}\n")
            else:
                self.all_logs_text.insert(tk.END, f"[{timestamp}] ОТВЕТ {log['provider']}:\n")
                self.all_logs_text.insert(tk.END, f"📥 {log['response']}\n")
                self.all_logs_text.insert(tk.END, f"Токены: {log['input_tokens']}+{log['output_tokens']}\n")
            self.all_logs_text.insert(tk.END, "-" * 50 + "\n")
        
        self.all_logs_text.config(state=tk.DISABLED)

    def on_closing(self):
        """Обработчик закрытия окна"""
        # Останавливаем сервер если он запущен
        if self.server_running:
            self.stop_server()

        # Останавливаем обновление логов
        self.stop_log_updates = True
        if hasattr(self, 'log_update_thread') and self.log_update_thread and self.log_update_thread.is_alive():
            self.log_update_thread.join(timeout=2.0)

        # Закрываем окно
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    gui = ProxyGUI(root)
    root.mainloop()