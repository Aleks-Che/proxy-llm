import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import requests
import time
import os
from server import app
import uvicorn
from config import config as Config

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
                'total_cost': 'Total Cost: {cost}',
                'logs_frame': 'Request and Response Logs',
                'save_logs_checkbox': 'Save logs to file',
                'requests_tab': 'User Requests',
                'responses_tab': 'LLM Responses',
                'all_logs_tab': 'All Logs',
                'language_frame': 'Language',
                'language_en': 'English',
                'language_ru': 'Русский',
                'language_zh': '中文',
                'language_es': 'Español',
                'language_hi': 'हिन्दी',
                'language_ar': 'العربية',
                'language_bn': 'বাংলা',
                'language_pt': 'Português',
                'language_ja': '日本語',
                'language_de': 'Deutsch',
                'model_label': 'Model:',
                'settings_button': '⚙ Settings',
                'settings_window_title': 'Settings',
                'providers_tab': 'Providers',
                'logs_tab': 'Logs',
                'language_tab': 'Language',
                'cancel_button': 'Cancel',
                'save_button': 'Save',
                'enabled_checkbox': 'Enabled',
                'api_key_label': 'API Key:',
                'models_label': 'Models:',
                'save_logs_checkbox': 'Save logs to file',
                'log_file_label': 'Log file path:',
                'max_size_label': 'Maximum file size (bytes):',
                'language_selection_label': 'Select interface language:'
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
                'total_cost': 'Общая стоимость: {cost}',
                'logs_frame': 'Логи запросов и ответов',
                'save_logs_checkbox': 'Сохранять логи в файл',
                'requests_tab': 'Запросы пользователя',
                'responses_tab': 'Ответы LLM',
                'all_logs_tab': 'Все логи',
                'language_frame': 'Язык',
                'language_en': 'English',
                'language_ru': 'Русский',
                'language_zh': '中文',
                'language_es': 'Español',
                'language_hi': 'हिन्दी',
                'language_ar': 'العربية',
                'language_bn': 'বাংলা',
                'language_pt': 'Português',
                'language_ja': '日本語',
                'language_de': 'Deutsch',
                'model_label': 'Модель:',
                'settings_button': '⚙ Настройки',
                'settings_window_title': 'Настройки',
                'providers_tab': 'Провайдеры',
                'logs_tab': 'Логи',
                'language_tab': 'Язык',
                'cancel_button': 'Отмена',
                'save_button': 'Сохранить',
                'enabled_checkbox': 'Включен',
                'api_key_label': 'API ключ:',
                'models_label': 'Модели:',
                'save_logs_checkbox': 'Сохранять логи в файл',
                'log_file_label': 'Путь к файлу логов:',
                'max_size_label': 'Максимальный размер файла (байт):',
                'language_selection_label': 'Выберите язык интерфейса:'
            },
            'zh': {
                'title': 'LLM 代理',
                'provider_frame': '提供商选择',
                'provider_label': '提供商：',
                'start_button': '▶ 启动',
                'stop_button': '⏹ 停止',
                'port_label': '端口：{port}',
                'stats_frame': '统计',
                'total_requests': '总请求数：{count}',
                'total_tokens': '总令牌数：{count}',
                'total_cost': '总成本：{cost}',
                'logs_frame': '请求和响应日志',
                'save_logs_checkbox': '将日志保存到文件',
                'requests_tab': '用户请求',
                'responses_tab': 'LLM 响应',
                'all_logs_tab': '所有日志',
                'language_frame': '语言',
                'language_en': 'English',
                'language_ru': 'Русский',
                'language_zh': '中文',
                'language_es': 'Español',
                'language_hi': 'हिन्दी',
                'language_ar': 'العربية',
                'language_bn': 'বাংলা',
                'language_pt': 'Português',
                'language_ja': '日本語',
                'language_de': 'Deutsch',
                'model_label': '模型：',
                'settings_button': '⚙ 设置',
                'settings_window_title': '设置',
                'providers_tab': '提供商',
                'logs_tab': '日志',
                'language_tab': '语言',
                'cancel_button': '取消',
                'save_button': '保存',
                'enabled_checkbox': '启用',
                'api_key_label': 'API 密钥：',
                'models_label': '模型：',
                'save_logs_checkbox': '将日志保存到文件',
                'log_file_label': '日志文件路径：',
                'max_size_label': '最大文件大小（字节）：',
                'language_selection_label': '选择界面语言：'
            },
            'es': {
                'title': 'Proxy LLM',
                'provider_frame': 'Selección de Proveedor',
                'provider_label': 'Proveedor:',
                'start_button': '▶ Iniciar',
                'stop_button': '⏹ Detener',
                'port_label': 'Puerto: {port}',
                'stats_frame': 'Estadísticas',
                'total_requests': 'Total de Solicitudes: {count}',
                'total_tokens': 'Total de Tokens: {count}',
                'total_cost': 'Costo Total: {cost}',
                'logs_frame': 'Registros de Solicitudes y Respuestas',
                'save_logs_checkbox': 'Guardar registros en archivo',
                'requests_tab': 'Solicitudes del Usuario',
                'responses_tab': 'Respuestas LLM',
                'all_logs_tab': 'Todos los Registros',
                'language_frame': 'Idioma',
                'language_en': 'English',
                'language_ru': 'Русский',
                'model_label': 'Modelo:',
                'settings_button': '⚙ Configuración',
                'settings_window_title': 'Configuración',
                'providers_tab': 'Proveedores',
                'logs_tab': 'Registros',
                'language_tab': 'Idioma',
                'cancel_button': 'Cancelar',
                'save_button': 'Guardar',
                'enabled_checkbox': 'Habilitado',
                'api_key_label': 'Clave API:',
                'models_label': 'Modelos:',
                'save_logs_checkbox': 'Guardar registros en archivo',
                'log_file_label': 'Ruta del archivo de registros:',
                'max_size_label': 'Tamaño máximo del archivo (bytes):',
                'language_selection_label': 'Seleccione el idioma de la interfaz:'
            },
            'hi': {
                'title': 'LLM प्रॉक्सी',
                'provider_frame': 'प्रदाता चयन',
                'provider_label': 'प्रदाता:',
                'start_button': '▶ शुरू करें',
                'stop_button': '⏹ रोकें',
                'port_label': 'पोर्ट: {port}',
                'stats_frame': 'सांख्यिकी',
                'total_requests': 'कुल अनुरोध: {count}',
                'total_tokens': 'कुल टोकन: {count}',
                'total_cost': 'कुल लागत: {cost}',
                'logs_frame': 'अनुरोध और प्रतिक्रिया लॉग',
                'save_logs_checkbox': 'लॉग को फ़ाइल में सहेजें',
                'requests_tab': 'उपयोगकर्ता अनुरोध',
                'responses_tab': 'LLM प्रतिक्रियाएँ',
                'all_logs_tab': 'सभी लॉग',
                'language_frame': 'भाषा',
                'language_en': 'English',
                'language_ru': 'Русский',
                'language_zh': '中文',
                'language_es': 'Español',
                'language_hi': 'हिन्दी',
                'language_ar': 'العربية',
                'language_bn': 'বাংলা',
                'language_pt': 'Português',
                'language_ja': '日本語',
                'language_de': 'Deutsch',
                'model_label': 'मॉडल:',
                'settings_button': '⚙ सेटिंग्स',
                'settings_window_title': 'सेटिंग्स',
                'providers_tab': 'प्रदाता',
                'logs_tab': 'लॉग',
                'language_tab': 'भाषा',
                'cancel_button': 'रद्द करें',
                'save_button': 'सहेजें',
                'enabled_checkbox': 'सक्षम',
                'api_key_label': 'API कुंजी:',
                'models_label': 'मॉडल:',
                'save_logs_checkbox': 'लॉग को फ़ाइल में सहेजें',
                'log_file_label': 'लॉग फ़ाइल पथ:',
                'max_size_label': 'अधिकतम फ़ाइल आकार (बाइट):',
                'language_selection_label': 'इंटरफ़ेस भाषा चुनें:'
            },
            'ar': {
                'title': 'وكيل LLM',
                'provider_frame': 'اختيار المزود',
                'provider_label': 'المزود:',
                'start_button': '▶ بدء',
                'stop_button': '⏹ إيقاف',
                'port_label': 'المنفذ: {port}',
                'stats_frame': 'الإحصائيات',
                'total_requests': 'إجمالي الطلبات: {count}',
                'total_tokens': 'إجمالي الرموز: {count}',
                'total_cost': 'التكلفة الإجمالية: {cost}',
                'logs_frame': 'سجلات الطلبات والردود',
                'save_logs_checkbox': 'حفظ السجلات في ملف',
                'requests_tab': 'طلبات المستخدم',
                'responses_tab': 'ردود LLM',
                'all_logs_tab': 'جميع السجلات',
                'language_frame': 'اللغة',
                'language_en': 'English',
                'language_ru': 'Русский',
                'language_zh': '中文',
                'language_es': 'Español',
                'language_hi': 'हिन्दी',
                'language_ar': 'العربية',
                'language_bn': 'বাংলা',
                'language_pt': 'Português',
                'language_ja': '日本語',
                'language_de': 'Deutsch',
                'model_label': 'النموذج:',
                'settings_button': '⚙ الإعدادات',
                'settings_window_title': 'الإعدادات',
                'providers_tab': 'المزودون',
                'logs_tab': 'السجلات',
                'language_tab': 'اللغة',
                'cancel_button': 'إلغاء',
                'save_button': 'حفظ',
                'enabled_checkbox': 'مفعل',
                'api_key_label': 'مفتاح API:',
                'models_label': 'النماذج:',
                'save_logs_checkbox': 'حفظ السجلات في ملف',
                'log_file_label': 'مسار ملف السجل:',
                'max_size_label': 'الحد الأقصى لحجم الملف (بايت):',
                'language_selection_label': 'اختر لغة الواجهة:'
            },
            'bn': {
                'title': 'LLM প্রক্সি',
                'provider_frame': 'প্রদানকারী নির্বাচন',
                'provider_label': 'প্রদানকারী:',
                'start_button': '▶ শুরু করুন',
                'stop_button': '⏹ বন্ধ করুন',
                'port_label': 'পোর্ট: {port}',
                'stats_frame': 'পরিসংখ্যান',
                'total_requests': 'মোট অনুরোধ: {count}',
                'total_tokens': 'মোট টোকেন: {count}',
                'total_cost': 'মোট খরচ: {cost}',
                'logs_frame': 'অনুরোধ এবং প্রতিক্রিয়া লগ',
                'save_logs_checkbox': 'লগ ফাইলে সংরক্ষণ করুন',
                'requests_tab': 'ব্যবহারকারীর অনুরোধ',
                'responses_tab': 'LLM প্রতিক্রিয়া',
                'all_logs_tab': 'সমস্ত লগ',
                'language_frame': 'ভাষা',
                'language_en': 'English',
                'language_ru': 'Русский',
                'language_zh': '中文',
                'language_es': 'Español',
                'language_hi': 'हिन्दी',
                'language_ar': 'العربية',
                'language_bn': 'বাংলা',
                'language_pt': 'Português',
                'language_ja': '日本語',
                'language_de': 'Deutsch',
                'model_label': 'মডেল:',
                'settings_button': '⚙ সেটিংস',
                'settings_window_title': 'সেটিংস',
                'providers_tab': 'প্রদানকারী',
                'logs_tab': 'লগ',
                'language_tab': 'ভাষা',
                'cancel_button': 'বাতিল করুন',
                'save_button': 'সংরক্ষণ করুন',
                'enabled_checkbox': 'সক্ষম',
                'api_key_label': 'API কী:',
                'models_label': 'মডেল:',
                'save_logs_checkbox': 'লগ ফাইলে সংরক্ষণ করুন',
                'log_file_label': 'লগ ফাইল পথ:',
                'max_size_label': 'সর্বাধিক ফাইল আকার (বাইট):',
                'language_selection_label': 'ইন্টারফেস ভাষা নির্বাচন করুন:'
            },
            'pt': {
                'title': 'Proxy LLM',
                'provider_frame': 'Seleção de Provedor',
                'provider_label': 'Provedor:',
                'start_button': '▶ Iniciar',
                'stop_button': '⏹ Parar',
                'port_label': 'Porta: {port}',
                'stats_frame': 'Estatísticas',
                'total_requests': 'Total de Solicitações: {count}',
                'total_tokens': 'Total de Tokens: {count}',
                'total_cost': 'Custo Total: {cost}',
                'logs_frame': 'Registros de Solicitações e Respostas',
                'save_logs_checkbox': 'Salvar registros em arquivo',
                'requests_tab': 'Solicitações do Usuário',
                'responses_tab': 'Respostas LLM',
                'all_logs_tab': 'Todos os Registros',
                'language_frame': 'Idioma',
                'language_en': 'English',
                'language_ru': 'Русский',
                'language_zh': '中文',
                'language_es': 'Español',
                'language_hi': 'हिन्दी',
                'language_ar': 'العربية',
                'language_bn': 'বাংলা',
                'language_pt': 'Português',
                'language_ja': '日本語',
                'language_de': 'Deutsch',
                'language_zh': '中文',
                'language_es': 'Español',
                'language_hi': 'हिन्दी',
                'language_ar': 'العربية',
                'language_bn': 'বাংলা',
                'language_pt': 'Português',
                'language_ja': '日本語',
                'language_de': 'Deutsch',
                'model_label': 'Modelo:',
                'settings_button': '⚙ Configurações',
                'settings_window_title': 'Configurações',
                'providers_tab': 'Provedores',
                'logs_tab': 'Registros',
                'language_tab': 'Idioma',
                'cancel_button': 'Cancelar',
                'save_button': 'Salvar',
                'enabled_checkbox': 'Habilitado',
                'api_key_label': 'Chave API:',
                'models_label': 'Modelos:',
                'save_logs_checkbox': 'Salvar registros em arquivo',
                'log_file_label': 'Caminho do arquivo de registros:',
                'max_size_label': 'Tamanho máximo do arquivo (bytes):',
                'language_selection_label': 'Selecione o idioma da interface:'
            },
            'ja': {
                'title': 'LLM プロキシ',
                'provider_frame': 'プロバイダー選択',
                'provider_label': 'プロバイダー:',
                'start_button': '▶ 開始',
                'stop_button': '⏹ 停止',
                'port_label': 'ポート: {port}',
                'stats_frame': '統計',
                'total_requests': '総リクエスト数: {count}',
                'total_tokens': '総トークン数: {count}',
                'total_cost': '総コスト: {cost}',
                'logs_frame': 'リクエストおよびレスポンスログ',
                'save_logs_checkbox': 'ログをファイルに保存',
                'requests_tab': 'ユーザーリクエスト',
                'responses_tab': 'LLM レスポンス',
                'all_logs_tab': 'すべてのログ',
                'language_frame': '言語',
                'language_en': 'English',
                'language_ru': 'Русский',
                'language_zh': '中文',
                'language_es': 'Español',
                'language_hi': 'हिन्दी',
                'language_ar': 'العربية',
                'language_bn': 'বাংলা',
                'language_pt': 'Português',
                'language_ja': '日本語',
                'language_de': 'Deutsch',
                'model_label': 'モデル:',
                'settings_button': '⚙ 設定',
                'settings_window_title': '設定',
                'providers_tab': 'プロバイダー',
                'logs_tab': 'ログ',
                'language_tab': '言語',
                'cancel_button': 'キャンセル',
                'save_button': '保存',
                'enabled_checkbox': '有効',
                'api_key_label': 'API キー:',
                'models_label': 'モデル:',
                'save_logs_checkbox': 'ログをファイルに保存',
                'log_file_label': 'ログファイルのパス:',
                'max_size_label': '最大ファイルサイズ（バイト）:',
                'language_selection_label': 'インターフェース言語を選択:'
            },
            'de': {
                'title': 'LLM Proxy',
                'provider_frame': 'Anbieterauswahl',
                'provider_label': 'Anbieter:',
                'start_button': '▶ Starten',
                'stop_button': '⏹ Stoppen',
                'port_label': 'Port: {port}',
                'stats_frame': 'Statistiken',
                'total_requests': 'Gesamt Anfragen: {count}',
                'total_tokens': 'Gesamt Tokens: {count}',
                'total_cost': 'Gesamtkosten: {cost}',
                'logs_frame': 'Anfrage- und Antwortprotokolle',
                'save_logs_checkbox': 'Protokolle in Datei speichern',
                'requests_tab': 'Benutzeranfragen',
                'responses_tab': 'LLM Antworten',
                'all_logs_tab': 'Alle Protokolle',
                'language_frame': 'Sprache',
                'language_en': 'English',
                'language_ru': 'Русский',
                'language_zh': '中文',
                'language_es': 'Español',
                'language_hi': 'हिन्दी',
                'language_ar': 'العربية',
                'language_bn': 'বাংলা',
                'language_pt': 'Português',
                'language_ja': '日本語',
                'language_de': 'Deutsch',
                'model_label': 'Modell:',
                'settings_button': '⚙ Einstellungen',
                'settings_window_title': 'Einstellungen',
                'providers_tab': 'Anbieter',
                'logs_tab': 'Protokolle',
                'language_tab': 'Sprache',
                'cancel_button': 'Abbrechen',
                'save_button': 'Speichern',
                'enabled_checkbox': 'Aktiviert',
                'api_key_label': 'API-Schlüssel:',
                'models_label': 'Modelle:',
                'save_logs_checkbox': 'Protokolle in Datei speichern',
                'log_file_label': 'Pfad der Protokolldatei:',
                'max_size_label': 'Maximale Dateigröße (Bytes):',
                'language_selection_label': 'Schnittstellensprache auswählen:'
            }
        }

        # Переменные
        self.current_provider = tk.StringVar(value=Config.get_default_provider())
        self.current_model = tk.StringVar()
        default_lang = Config.get_language()  # Читаем из settings.json
        self.current_language = tk.StringVar(value=default_lang)
        self.server_running = False
        self.server_process = None
        self.stop_server_flag = False
        logging_config = Config.get_logging_config()
        self.save_logs_to_file = tk.BooleanVar(value=logging_config.get("save_to_file", False))

        # Ссылки на виджеты для обновления текстов
        self.provider_frame = None
        self.language_frame = None
        self.provider_label = None
        self.model_label = None
        self.provider_combo = None
        self.model_combo = None
        self.settings_button = None
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

        # Флаг для отслеживания открытого окна настроек
        self.settings_window_open = False

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
        # Получаем список доступных провайдеров из настроек
        providers_config = Config.get_providers()
        available_providers = [name for name, config in providers_config.items() if config.get("enabled", False)]
        provider_combo = ttk.Combobox(self.provider_frame, textvariable=self.current_provider, values=available_providers)
        provider_combo.grid(row=0, column=1, padx=5, pady=5)
        provider_combo.bind("<<ComboboxSelected>>", self.change_provider)

        # Лейбл для модели
        self.model_label = ttk.Label(self.provider_frame, text="")
        self.model_label.grid(row=0, column=2, padx=5, pady=5)
        self.model_combo = ttk.Combobox(self.provider_frame, textvariable=self.current_model, width=20)
        self.model_combo.grid(row=0, column=3, padx=5, pady=5)
        self.model_combo.bind("<<ComboboxSelected>>", self.change_model)

        # Кнопка запуска/остановки сервера с иконкой
        self.start_button = ttk.Button(self.provider_frame, text="", command=self.toggle_server, width=15)
        self.start_button.grid(row=0, column=4, padx=5, pady=5)

        # Лейбл для отображения порта
        self.port_label = ttk.Label(self.provider_frame, text="")
        self.port_label.grid(row=0, column=5, padx=5, pady=5)

        # Кнопка настроек (справа)
        self.settings_button = ttk.Button(top_frame, text="", command=self.open_settings)
        self.settings_button.pack(side="right", padx=(10, 0))

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

        # Инициализируем список моделей
        self.update_models_list()

    def change_provider(self, event):
        provider = self.current_provider.get()
        # Обновляем список моделей для нового провайдера
        self.update_models_list()

        try:
            server_config = Config.get_server_config()
            port = server_config.get("port", 8000)
            response = requests.post(f"http://localhost:{port}/switch-provider/{provider}")
            if response.status_code == 200:
                print(f"Провайдер изменен на {provider}")
            else:
                print("Ошибка изменения провайдера")
        except:
            print("Сервер не запущен")

    def change_language(self):
        """Переключение языка интерфейса"""
        lang = self.current_language.get()
        # Сохраняем новый язык в settings.json
        Config._settings["language"] = lang
        Config.save_settings()
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
        if self.model_label:
            self.model_label.config(text=trans['model_label'])
        if self.start_button:
            text = trans['start_button'] if not self.server_running else trans['stop_button']
            self.start_button.config(text=text)
        if self.settings_button:
            self.settings_button.config(text=trans['settings_button'])
        server_config = Config.get_server_config()
        if self.port_label:
            self.port_label.config(text=trans['port_label'].format(port=server_config.get("port", 8000)))

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
            server_config = Config.get_server_config()
            cmd = [sys.executable, "-c", f"""
import sys
sys.path.insert(0, r"{os.getcwd()}")
import uvicorn
from server import app
from config import config as Config
uvicorn.run(app, host="{server_config['host']}", port={server_config['port']})
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
                server_config = Config.get_server_config()
                port = server_config.get("port", 8000)
                response = requests.get(f"http://localhost:{port}/stats", timeout=2)
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
            server_config = Config.get_server_config()
            port = server_config.get("port", 8000)

            # Получаем логи запросов
            response = requests.get(f"http://localhost:{port}/logs/requests", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"Получено запросов: {len(data['request_logs'])}")
                # Обновляем в основном потоке GUI
                self.root.after(0, lambda: self.update_requests_text(data['request_logs']))

            # Получаем логи ответов
            response = requests.get(f"http://localhost:{port}/logs/responses", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"Получено ответов: {len(data['response_logs'])}")
                self.root.after(0, lambda: self.update_responses_text(data['response_logs']))

            # Получаем все логи
            response = requests.get(f"http://localhost:{port}/logs/all", timeout=2)
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
                logging_config = Config.get_logging_config()
                log_file_path = logging_config.get("file_path", "logs/proxy_logs.txt")
                log_max_size = logging_config.get("max_size", 10485760)

                os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

                # Проверяем размер файла
                if os.path.exists(log_file_path):
                    file_size = os.path.getsize(log_file_path)
                    if file_size > log_max_size:
                        # Очищаем файл, если он превышает лимит
                        with open(log_file_path, 'w', encoding='utf-8') as f:
                            f.write("")
                        print(f"Файл логов очищен (превышен размер {log_max_size} байт)")

                # Добавляем новые логи в конец файла
                with open(log_file_path, 'a', encoding='utf-8') as f:
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

    def change_model(self, event):
        """Обработчик изменения модели"""
        model = self.current_model.get()
        print(f"Модель изменена на {model}")

    def open_settings(self):
        """Открытие окна настроек"""
        if self.settings_window_open:
            return  # Если окно уже открыто, не открываем новое

        # Получаем текущий язык для переводов
        current_lang = self.current_language.get()
        trans = self.translations[current_lang]

        settings_window = tk.Toplevel(self.root)
        settings_window.title(trans['settings_window_title'])
        settings_window.geometry("700x500")

        # Делаем окно модальным
        settings_window.grab_set()
        settings_window.focus_set()

        # Устанавливаем флаг
        self.settings_window_open = True

        # Обработчик закрытия окна
        settings_window.protocol("WM_DELETE_WINDOW", lambda: self.on_settings_close(settings_window))

        # Создаем notebook для вкладок настроек
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Вкладка провайдеров
        providers_frame = self.create_providers_tab(notebook, trans)
        notebook.add(providers_frame, text=trans['providers_tab'])

        # Вкладка логов
        logs_frame = self.create_logs_tab(notebook, trans)
        notebook.add(logs_frame, text=trans['logs_tab'])

        # Вкладка языка
        language_frame = self.create_language_tab(notebook, trans)
        notebook.add(language_frame, text=trans['language_tab'])

        # Кнопки внизу
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(button_frame, text=trans['cancel_button'], command=lambda: self.on_settings_close(settings_window)).pack(side="left", padx=5)
        ttk.Button(button_frame, text=trans['save_button'], command=lambda: self.save_settings(settings_window)).pack(side="right", padx=5)

    def create_providers_tab(self, parent, trans):
        """Создание вкладки провайдеров"""
        frame = ttk.Frame(parent)

        # Canvas для прокрутки
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Получаем настройки провайдеров
        providers_config = Config.get_providers()

        self.provider_widgets = {}  # Для хранения виджетов

        row = 0
        for provider_name, provider_config in providers_config.items():
            # Фрейм для провайдера
            provider_frame = ttk.LabelFrame(scrollable_frame, text=provider_config.get("name", provider_name))
            provider_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
            provider_frame.columnconfigure(1, weight=1)

            # Чекбокс включения
            enabled_var = tk.BooleanVar(value=provider_config.get("enabled", False))
            ttk.Checkbutton(provider_frame, text=trans['enabled_checkbox'], variable=enabled_var).grid(row=0, column=0, padx=5, pady=2)

            # API ключ
            ttk.Label(provider_frame, text=trans['api_key_label']).grid(row=1, column=0, sticky="w", padx=5, pady=2)
            api_key_var = tk.StringVar(value=provider_config.get("api_key", ""))
            api_entry = ttk.Entry(provider_frame, textvariable=api_key_var, show="*")
            api_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

            # Модели
            ttk.Label(provider_frame, text=trans['models_label']).grid(row=2, column=0, sticky="w", padx=5, pady=2)
            models_text = tk.Text(provider_frame, height=3, width=50)
            models_text.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

            # Заполняем модели
            models = provider_config.get("models", [])
            models_content = ""
            for model in models:
                models_content += f"{model['name']} (context: {model['context_window']})\n"
            models_text.insert("1.0", models_content.strip())
            models_text.config(state="disabled")

            # Сохраняем виджеты
            self.provider_widgets[provider_name] = {
                "enabled": enabled_var,
                "api_key": api_key_var,
                "models_text": models_text
            }

            row += 1

        # Упаковка canvas и scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return frame

    def create_logs_tab(self, parent, trans):
        """Создание вкладки логов"""
        frame = ttk.Frame(parent)

        logging_config = Config.get_logging_config()

        # Сохранение в файл
        self.save_logs_var = tk.BooleanVar(value=logging_config.get("save_to_file", False))
        ttk.Checkbutton(frame, text=trans['save_logs_checkbox'], variable=self.save_logs_var).pack(anchor="w", padx=10, pady=5)

        # Путь к файлу
        ttk.Label(frame, text=trans['log_file_label']).pack(anchor="w", padx=10, pady=2)
        self.log_file_var = tk.StringVar(value=logging_config.get("file_path", "logs/proxy_logs.txt"))
        ttk.Entry(frame, textvariable=self.log_file_var).pack(fill="x", padx=10, pady=2)

        # Максимальный размер
        ttk.Label(frame, text=trans['max_size_label']).pack(anchor="w", padx=10, pady=2)
        self.log_max_size_var = tk.StringVar(value=str(logging_config.get("max_size", 10485760)))
        ttk.Entry(frame, textvariable=self.log_max_size_var).pack(fill="x", padx=10, pady=2)

        return frame

    def create_language_tab(self, parent, trans):
        """Создание вкладки языка"""
        frame = ttk.Frame(parent)

        ttk.Label(frame, text=trans['language_selection_label'], font=("Arial", 12)).pack(pady=20)

        self.settings_lang_var = tk.StringVar(value=Config.get_language())

        ttk.Radiobutton(frame, text=trans['language_en'], variable=self.settings_lang_var, value="en").pack(pady=5)
        ttk.Radiobutton(frame, text=trans['language_ru'], variable=self.settings_lang_var, value="ru").pack(pady=5)
        ttk.Radiobutton(frame, text=trans['language_zh'], variable=self.settings_lang_var, value="zh").pack(pady=5)
        ttk.Radiobutton(frame, text=trans['language_es'], variable=self.settings_lang_var, value="es").pack(pady=5)
        ttk.Radiobutton(frame, text=trans['language_hi'], variable=self.settings_lang_var, value="hi").pack(pady=5)
        ttk.Radiobutton(frame, text=trans['language_ar'], variable=self.settings_lang_var, value="ar").pack(pady=5)
        ttk.Radiobutton(frame, text=trans['language_bn'], variable=self.settings_lang_var, value="bn").pack(pady=5)
        ttk.Radiobutton(frame, text=trans['language_pt'], variable=self.settings_lang_var, value="pt").pack(pady=5)
        ttk.Radiobutton(frame, text=trans['language_ja'], variable=self.settings_lang_var, value="ja").pack(pady=5)
        ttk.Radiobutton(frame, text=trans['language_de'], variable=self.settings_lang_var, value="de").pack(pady=5)

        return frame

    def save_settings(self, window):
        """Сохранение настроек"""
        # Сохраняем настройки провайдеров
        if hasattr(self, 'provider_widgets'):
            providers_config = Config.get_providers()
            for provider_name, widgets in self.provider_widgets.items():
                if provider_name in providers_config:
                    providers_config[provider_name]["enabled"] = widgets["enabled"].get()
                    providers_config[provider_name]["api_key"] = widgets["api_key"].get()

        # Сохраняем настройки логов
        if hasattr(self, 'save_logs_var'):
            logging_config = Config.get_logging_config()
            logging_config["save_to_file"] = self.save_logs_var.get()
            logging_config["file_path"] = self.log_file_var.get()
            try:
                logging_config["max_size"] = int(self.log_max_size_var.get())
            except ValueError:
                logging_config["max_size"] = 10485760

        # Сохраняем язык
        if hasattr(self, 'settings_lang_var'):
            new_lang = self.settings_lang_var.get()
            Config._settings["language"] = new_lang
            self.current_language.set(new_lang)  # Обновляем текущий язык
            self.change_language()  # Применяем изменения языка

        Config.save_settings()
        self.settings_window_open = False
        window.destroy()
        print("Настройки сохранены")

        # Обновляем GUI
        self.update_available_providers()
        self.update_models_list()

    def on_settings_close(self, window):
        """Обработчик закрытия окна настроек"""
        self.settings_window_open = False
        window.destroy()

    def update_models_list(self):
        """Обновление списка моделей для текущего провайдера"""
        provider = self.current_provider.get()
        if provider:
            provider_config = Config.get_provider_config(provider)
            models = provider_config.get("models", [])
            model_names = [model["name"] for model in models]
            if hasattr(self, 'model_combo'):
                self.model_combo['values'] = model_names
                if model_names:
                    self.current_model.set(model_names[0])

    def update_available_providers(self):
        """Обновление списка доступных провайдеров"""
        providers_config = Config.get_providers()
        available_providers = [name for name, config in providers_config.items() if config.get("enabled", False)]
        if hasattr(self, 'provider_combo') and self.provider_combo:
            self.provider_combo['values'] = available_providers
            # Если текущий провайдер больше не доступен, выбираем первый доступный
            if self.current_provider.get() not in available_providers and available_providers:
                self.current_provider.set(available_providers[0])
                self.update_models_list()

if __name__ == "__main__":
    root = tk.Tk()
    gui = ProxyGUI(root)
    root.mainloop()