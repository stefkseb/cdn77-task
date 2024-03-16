import requests
import json

payload = {'query': 'node_load1'}
# res = requests.get('http://127.0.0.1:9090/api/v1/query', params=payload)
res = requests.get('http://192.168.50.145:9090/api/v1/query', params=payload)

data_to_write = {
        "monitoring": [],
        "nginx": []
}

data_json = json.loads(res.text)
for rec in data_json["data"]["result"]:
        data_to_write["monitoring"].append({rec["metric"]["instance"]: float(rec["value"][1])})

print(json.dumps(data_to_write, indent=4))