#!/usr/bin/env python3
"""
Скрипт для проверки, что использует порт 8000
"""

import socket
import subprocess
import sys

def check_port_8000():
    """Проверяем, занят ли порт 8000"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 8000))
    sock.close()

    if result == 0:
        print("✓ Порт 8000 занят")
        return True
    else:
        print("✗ Порт 8000 свободен")
        return False

def get_process_using_port():
    """Получаем процесс, использующий порт 8000"""
    try:
        if sys.platform == "win32":
            # Windows
            result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if ':8000' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        print(f"Найден процесс с PID {pid} на порту 8000")

                        # Получаем имя процесса
                        try:
                            task_result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], capture_output=True, text=True)
                            for task_line in task_result.stdout.split('\n'):
                                if pid in task_line:
                                    print(f"Процесс: {task_line}")
                                    break
                        except:
                            print("Не удалось определить имя процесса")
                        return pid
        else:
            # Linux/Mac
            result = subprocess.run(['lsof', '-i', ':8000'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines[1:]:  # Пропускаем заголовок
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = parts[1]
                            process_name = parts[0]
                            print(f"Найден процесс {process_name} (PID {pid}) на порту 8000")
                            return pid
    except Exception as e:
        print(f"Ошибка при проверке процессов: {e}")

    return None

if __name__ == "__main__":
    print("=== Проверка порта 8000 ===")
    is_occupied = check_port_8000()

    if is_occupied:
        print("\nПроверяем, какой процесс использует порт...")
        pid = get_process_using_port()

        if pid:
            print(f"\nЧтобы освободить порт, можно завершить процесс с PID {pid}")
            if sys.platform == "win32":
                print(f"Команда: taskkill /PID {pid} /F")
            else:
                print(f"Команда: kill -9 {pid}")
        else:
            print("Не удалось определить процесс")
    else:
        print("Порт свободен, можно запускать сервер")