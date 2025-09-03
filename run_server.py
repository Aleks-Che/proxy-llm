#!/usr/bin/env python3
"""
Скрипт для запуска сервера в фоне
"""

import subprocess
import sys
import time
import signal
import os

def run_server():
    """Запуск сервера"""
    print("Запуск LLM Proxy сервера...")

    # Запуск сервера в фоне
    try:
        process = subprocess.Popen([
            sys.executable, "server.py"
        ], cwd=os.path.dirname(os.path.abspath(__file__)))

        print(f"Сервер запущен с PID: {process.pid}")
        print("Сервер доступен по адресу: http://localhost:8000")
        print("Для остановки нажмите Ctrl+C")

        # Ожидание сигнала остановки
        def signal_handler(sig, frame):
            print("\nОстановка сервера...")
            process.terminate()
            process.wait()
            print("Сервер остановлен")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Ожидание завершения процесса
        process.wait()

    except KeyboardInterrupt:
        print("\nПолучен сигнал прерывания")
        if 'process' in locals():
            process.terminate()
            process.wait()
        print("Сервер остановлен")
    except Exception as e:
        print(f"Ошибка при запуске сервера: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()