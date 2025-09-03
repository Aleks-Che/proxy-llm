import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import requests
import time
import os
from server import app
import uvicorn
from config import Config
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

class ProxyGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LLM Proxy")
        self.root.geometry("1000x800")  # Увеличиваем размер окна

        # Словарь переводов
        self.translations = {
            'en': {
                'title': 'LLM Proxy',
                'provider_frame': 'Provider Selection',
                'provider_label': 'Provider:',
                'start_button': '▶ Start',
                'stop_button': '⏹ Stop',
                'port_label': 'Port: {port}',
                'stats_frame': 'Statistics',
                'total_requests': 'Total Requests: {count}',
                'total_tokens': 'Total Tokens: {count}',
                'total_cost': 'Total Cost: ${cost}',
                'logs_frame': 'Request and Response Logs',
                'save_logs_checkbox': 'Save logs to file',
                'requests_tab': 'User Requests',
                'responses_tab': 'LLM Responses',
                'all_logs_tab': 'All Logs',
                'language_frame': 'Language',
                'language_en': 'English',
                'language_ru': 'Русский'
            },
            'ru': {
                'title': 'LLM Прокси',
                'provider_frame': 'Выбор провайдера',
                'provider_label': 'Провайдер:',
                'start_button': '▶ Запустить',
                'stop_button': '⏹ Остановить',
                'port_label': 'Порт: {port}',
                'stats_frame': 'Статистика',
                'total_requests': 'Всего запросов: {count}',
                'total_tokens': 'Всего токенов: {count}',
                'total_cost': 'Общая стоимость: ${cost}',
                'logs_frame': 'Логи запросов и ответов',
                'save_logs_checkbox': 'Сохранять логи в файл',
                'requests_tab': 'Запросы пользователя',
                'responses_tab': 'Ответы LLM',
                'all_logs_tab': 'Все логи',
                'language_frame': 'Язык',
                'language_en': 'English',
                'language_ru': 'Русский'
            }
        }

        # Переменные
        self.current_provider = tk.StringVar(value=Config.DEFAULT_PROVIDER)
        default_lang = os.getenv('DEFAULT_LANGUAGE', 'en')  # Читаем из .env, по умолчанию 'en'
        self.current_language = tk.StringVar(value=default_lang)
        self.server_running = False
        self.server_process = None
        self.stop_server_flag = False
        self.save_logs_to_file = tk.BooleanVar(value=Config.SAVE_LOGS_TO_FILE)

        # Ссылки на виджеты для обновления текстов
        self.provider_frame = None
        self.language_frame = None
        self.provider_label = None
        self.start_button = None
        self.port_label = None
        self.stats_frame = None
        self.total_requests_label = None
        self.total_tokens_label = None
        self.total_cost_label = None
        self.logs_frame = None
        self.save_logs_checkbox = None
        self.notebook = None

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
        # Верхний фрейм для провайдера и языка
        top_frame = ttk.Frame(self.root)
        top_frame.pack(pady=10, padx=10, fill="x")

        # Фрейм для выбора провайдера (слева)
        self.provider_frame = ttk.LabelFrame(top_frame, text="")
        self.provider_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.provider_label = ttk.Label(self.provider_frame, text="")
        self.provider_label.grid(row=0, column=0, padx=5, pady=5)
        provider_combo = ttk.Combobox(self.provider_frame, textvariable=self.current_provider, values=["deepseek", "moonshot", "local"])
        provider_combo.grid(row=0, column=1, padx=5, pady=5)
        provider_combo.bind("<<ComboboxSelected>>", self.change_provider)

        # Кнопка запуска/остановки сервера с иконкой
        self.start_button = ttk.Button(self.provider_frame, text="", command=self.toggle_server, width=15)
        self.start_button.grid(row=0, column=2, padx=5, pady=5)

        # Лейбл для отображения порта
        self.port_label = ttk.Label(self.provider_frame, text="")
        self.port_label.grid(row=0, column=3, padx=5, pady=5)

        # Фрейм для выбора языка (справа)
        self.language_frame = ttk.LabelFrame(top_frame, text="")
        self.language_frame.pack(side="right", padx=(10, 0))

        ttk.Radiobutton(self.language_frame, text="English", variable=self.current_language, value="en", command=self.change_language).pack(side="left", padx=5, pady=5)
        ttk.Radiobutton(self.language_frame, text="Русский", variable=self.current_language, value="ru", command=self.change_language).pack(side="left", padx=5, pady=5)

        # Фрейм для статистики
        self.stats_frame = ttk.LabelFrame(self.root, text="")
        self.stats_frame.pack(pady=10, padx=10, fill="x")

        self.total_requests_label = ttk.Label(self.stats_frame, text="")
        self.total_requests_label.grid(row=0, column=0, padx=5, pady=5)

        self.total_tokens_label = ttk.Label(self.stats_frame, text="")
        self.total_tokens_label.grid(row=0, column=1, padx=5, pady=5)

        self.total_cost_label = ttk.Label(self.stats_frame, text="")
        self.total_cost_label.grid(row=0, column=2, padx=5, pady=5)

        # Фрейм для логов
        self.logs_frame = ttk.LabelFrame(self.root, text="")
        self.logs_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Чекбокс для сохранения логов в файл
        self.save_logs_checkbox = ttk.Checkbutton(self.logs_frame, text="", variable=self.save_logs_to_file)
        self.save_logs_checkbox.pack(pady=5, padx=5, anchor="w")

        # Создаем notebook для вкладок
        self.notebook = ttk.Notebook(self.logs_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Вкладка запросов
        requests_frame = ttk.Frame(self.notebook)
        self.notebook.add(requests_frame, text="")
        
        self.requests_text = scrolledtext.ScrolledText(requests_frame, height=8, wrap=tk.WORD)
        self.requests_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.requests_text.config(state=tk.DISABLED)

        # Вкладка ответов
        responses_frame = ttk.Frame(self.notebook)
        self.notebook.add(responses_frame, text="")
        
        self.responses_text = scrolledtext.ScrolledText(responses_frame, height=8, wrap=tk.WORD)
        self.responses_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.responses_text.config(state=tk.DISABLED)

        # Вкладка всех логов
        all_logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(all_logs_frame, text="")
        
        self.all_logs_text = scrolledtext.ScrolledText(all_logs_frame, height=8, wrap=tk.WORD)
        self.all_logs_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.all_logs_text.config(state=tk.DISABLED)

        # Устанавливаем начальные тексты
        self.update_ui_texts()

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

    def change_language(self):
        """Переключение языка интерфейса"""
        lang = self.current_language.get()
        self.update_ui_texts()
        self.root.title(self.translations[lang]['title'])

    def update_ui_texts(self):
        """Обновление текстов интерфейса в соответствии с выбранным языком"""
        lang = self.current_language.get()
        trans = self.translations[lang]

        # Обновляем заголовок окна
        self.root.title(trans['title'])

        # Обновляем фреймы
        if self.provider_frame:
            self.provider_frame.config(text=trans['provider_frame'])
        if self.language_frame:
            self.language_frame.config(text=trans['language_frame'])
        if self.stats_frame:
            self.stats_frame.config(text=trans['stats_frame'])
        if self.logs_frame:
            self.logs_frame.config(text=trans['logs_frame'])

        # Обновляем лейблы и кнопки
        if self.provider_label:
            self.provider_label.config(text=trans['provider_label'])
        if self.start_button:
            text = trans['start_button'] if not self.server_running else trans['stop_button']
            self.start_button.config(text=text)
        if self.port_label:
            self.port_label.config(text=trans['port_label'].format(port=Config.SERVER_PORT))

        # Обновляем статистику с текущими значениями
        if self.total_requests_label and self.total_tokens_label and self.total_cost_label:
            # Получаем текущие значения из текста или сбрасываем
            try:
                current_requests = int(self.total_requests_label.cget('text').split(': ')[1]) if ':' in self.total_requests_label.cget('text') else 0
                current_tokens = int(self.total_tokens_label.cget('text').split(': ')[1]) if ':' in self.total_tokens_label.cget('text') else 0
                current_cost = self.total_cost_label.cget('text').split('$')[1] if '$' in self.total_cost_label.cget('text') else "0.00"
            except:
                current_requests = current_tokens = 0
                current_cost = "0.00"

            self.total_requests_label.config(text=trans['total_requests'].format(count=current_requests))
            self.total_tokens_label.config(text=trans['total_tokens'].format(count=current_tokens))
            self.total_cost_label.config(text=trans['total_cost'].format(cost=f"${current_cost}"))

        # Обновляем чекбокс
        if self.save_logs_checkbox:
            self.save_logs_checkbox.config(text=trans['save_logs_checkbox'])

        # Обновляем вкладки notebook
        if self.notebook:
            self.notebook.tab(0, text=trans['requests_tab'])
            self.notebook.tab(1, text=trans['responses_tab'])
            self.notebook.tab(2, text=trans['all_logs_tab'])

    def toggle_server(self):
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        if not self.server_running:
            self.server_running = True
            self.stop_server_flag = False
            lang = self.current_language.get()
            self.start_button.config(text=self.translations[lang]['stop_button'], state="normal")
            threading.Thread(target=self.run_server, daemon=True).start()

    def stop_server(self):
        if self.server_running:
            self.server_running = False
            self.stop_server_flag = True
            lang = self.current_language.get()
            self.start_button.config(text=self.translations[lang]['start_button'], state="normal")

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
            lang = self.current_language.get()
            self.root.after(0, lambda: self.start_button.config(text=self.translations[lang]['start_button'], state="normal"))

    def update_stats(self):
        lang = self.current_language.get()
        trans = self.translations[lang]

        if self.server_running and self.server_process and self.server_process.poll() is None:
            try:
                response = requests.get(f"http://localhost:{Config.SERVER_PORT}/stats", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    self.total_requests_label.config(text=trans['total_requests'].format(count=data['total_requests']))
                    self.total_tokens_label.config(text=trans['total_tokens'].format(count=data['total_tokens']))
                    self.total_cost_label.config(text=trans['total_cost'].format(cost=f"{data['total_cost']:.6f}"))
            except:
                pass
        else:
            # Если сервер не запущен или процесс умер, сбрасываем состояние
            if self.server_running:
                self.stop_server()
            # Сбрасываем статистику
            self.total_requests_label.config(text=trans['total_requests'].format(count=0))
            self.total_tokens_label.config(text=trans['total_tokens'].format(count=0))
            self.total_cost_label.config(text=trans['total_cost'].format(cost="$0.00"))

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

        log_content = ""
        for log in logs:  # Уже отсортированы по времени
            timestamp = time.strftime("%H:%M:%S", time.localtime(log['timestamp']))
            if log['type'] == 'request':
                line = f"[{timestamp}] ЗАПРОС {log['provider']}:\n📤 {log['user_message']}\n"
                self.all_logs_text.insert(tk.END, line)
                log_content += line
            else:
                line = f"[{timestamp}] ОТВЕТ {log['provider']}:\n📥 {log['response']}\nТокены: {log['input_tokens']}+{log['output_tokens']}\n"
                self.all_logs_text.insert(tk.END, line)
                log_content += line
            separator = "-" * 50 + "\n"
            self.all_logs_text.insert(tk.END, separator)
            log_content += separator

        self.all_logs_text.config(state=tk.DISABLED)

        # Сохранение в файл, если чекбокс активен
        if self.save_logs_to_file.get():
            try:
                os.makedirs(os.path.dirname(Config.LOG_FILE_PATH), exist_ok=True)

                # Проверяем размер файла
                if os.path.exists(Config.LOG_FILE_PATH):
                    file_size = os.path.getsize(Config.LOG_FILE_PATH)
                    if file_size > Config.LOG_MAX_SIZE:
                        # Очищаем файл, если он превышает лимит
                        with open(Config.LOG_FILE_PATH, 'w', encoding='utf-8') as f:
                            f.write("")
                        print(f"Файл логов очищен (превышен размер {Config.LOG_MAX_SIZE} байт)")

                # Добавляем новые логи в конец файла
                with open(Config.LOG_FILE_PATH, 'a', encoding='utf-8') as f:
                    f.write(log_content)
            except Exception as e:
                print(f"Ошибка сохранения логов в файл: {e}")

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