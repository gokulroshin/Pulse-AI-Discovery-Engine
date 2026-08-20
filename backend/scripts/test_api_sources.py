import urllib.request
import json

req = urllib.request.Request('http://127.0.0.1:8000/api/v1/opportunities', headers={'X-API-Key': 'pulse-secret-key-123'})
try:
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode('utf-8'))
    print("Response keys:", list(data.keys()) if isinstance(data, dict) else "List response")
    items = data.get("opportunities", []) if isinstance(data, dict) else data
    for item in items[:6]:
        print(f"#{item['rank']} [{item['label']}] -> Top Sources: {item['top_sources']}")
except Exception as e:
    print("Error:", e)
