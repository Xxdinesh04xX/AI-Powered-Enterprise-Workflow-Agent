import requests

# Test basic endpoints
try:
    # Health check
    r = requests.get('http://127.0.0.1:8000/health')
    print(f'Health: {r.status_code} - {r.json()["status"]}')
    
    # API info
    r = requests.get('http://127.0.0.1:8000/api/v1/info')
    print(f'Info: {r.status_code} - {r.json()["name"]}')
    
    # Statistics with API key
    headers = {'X-API-Key': 'dev-key-123'}
    r = requests.get('http://127.0.0.1:8000/api/v1/statistics', headers=headers)
    print(f'Stats: {r.status_code} - {r.json()["total_tasks"]} tasks')
    
    print("✅ API is working!")
    
except Exception as e:
    print(f"❌ API test failed: {e}")
