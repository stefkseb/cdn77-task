import requests
import json

payload = {'query': 'node_load1'}
res = requests.get('http://192.168.50.145:9090/api/v1/query', params=payload)

data_to_write = {
        "monitoring": {},
        "nginx": {
                "response_headers": {},
                "stats": {}
        }
}

data_json = res.json()
for rec in data_json["data"]["result"]:
        data_to_write["monitoring"][rec["metric"]["instance"]] = float(rec["value"][1])

res = requests.get('http://192.168.50.145:4545/stub_status')
data:str = res.text
headers = res.headers

data = data.split('\n')

active_connections = data[0].split(' ')[2]
conn_stats = data[2].strip().split(' ')
rw_stats = data[3].strip().split(' ')

data_to_write["nginx"]["stats"]["connections"] = active_connections
data_to_write["nginx"]["stats"]["accepts"] = conn_stats[0]
data_to_write["nginx"]["stats"]["handled"] = conn_stats[1]
data_to_write["nginx"]["stats"]["requests"] = conn_stats[2]
data_to_write["nginx"]["stats"]["reading"] = rw_stats[1]
data_to_write["nginx"]["stats"]["writing"] = rw_stats[3]
data_to_write["nginx"]["stats"]["waiting"] = rw_stats[5]

for k,v in headers.items():
        data_to_write["nginx"]["response_headers"][k] = v
        
with open("/var/log/stats", "w") as f:
        f.write(json.dumps(data_to_write, indent=4))