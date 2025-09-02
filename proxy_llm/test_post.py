#!/usr/bin/env python3

import requests
import json
import time

def test_post_request():
    url = "http://localhost:10005/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "test",
        "messages": [
            {"role": "user", "content": "hello"}
        ]
    }
    
    print("Testing POST request to:", url)
    print("Request data:", json.dumps(data, indent=2))
    
    try:
        start_time = time.time()
        response = requests.post(url, headers=headers, json=data, timeout=10)
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        print("Response headers:", dict(response.headers))
        print("Response content:", response.text)
        
    except requests.exceptions.Timeout:
        print("Request timed out after 10 seconds")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    test_post_request()