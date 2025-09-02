#!/usr/bin/env python3

import requests
import json
import time

def test_cline_format():
    """Тестируем различные форматы запросов, которые могут приходить от Cline"""
    
    test_cases = [
        {
            "name": "Basic OpenAI format",
            "data": {
                "model": "gpt-oss-120b",
                "messages": [{"role": "user", "content": "test"}],
                "temperature": 0.7,
                "max_tokens": 1000
            }
        },
        {
            "name": "Cline format with extra fields",
            "data": {
                "model": "gpt-oss-120b", 
                "messages": [{"role": "user", "content": "test"}],
                "temperature": 0.7,
                "max_tokens": 1000,
                "stream": False,
                "top_p": 1.0,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
        },
        {
            "name": "Minimal format",
            "data": {
                "model": "test",
                "messages": [{"role": "user", "content": "hello"}]
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n=== Testing: {test_case['name']} ===")
        print("Request data:", json.dumps(test_case['data'], indent=2))
        
        try:
            response = requests.post(
                "http://localhost:10005/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json=test_case['data'],
                timeout=5
            )
            
            print(f"Status: {response.status_code}")
            print("Response:", response.text)
            
        except requests.exceptions.Timeout:
            print("Timeout - request took too long")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_cline_format()