#!/usr/bin/env python3
"""
Простой отладочный тест
"""

import requests
import json

def debug_test():
    """Простой тест для отладки"""
    print("=== Debug Test ===")
    
    # Простой запрос
    payload = {
        "model": "gpt-oss-120b",
        "messages": [
            {
                "role": "user", 
                "content": "test"
            }
        ]
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Используем сессию для лучшего контроля
        session = requests.Session()
        response = session.post(
            "http://localhost:10004/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            print("✅ Success!")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ Timeout")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error")
    except Exception as e:
        print(f"❌ Other Error: {e}")

if __name__ == "__main__":
    debug_test()