from flask import Flask
from flask_restful import Api, Resource
from apscheduler.schedulers.background import BackgroundScheduler

import docker
import socket, requests as req, json
import ast
import copy

# docker
client = docker.from_env()

# Flask
app = Flask(__name__)
api = Api(app)

NUM_OF_ORGS = 3
NUM_OF_PEERS = 2

global cpu_info
global mem_info
global net_info

def get_prometheus_ip_address():
    containers = client.containers.list()
    for container in containers:
        if str(container.name).startswith('prometheus'):
            return container.attrs["NetworkSettings"]["Networks"]["net_fabric"]["IPAddress"]

def get_cpu_info():
    global cpu_info
    temp_cpu_info = []
    idx = 0
    prometheus_ip_address = get_prometheus_ip_address()
    # order: peer0.org1 -> peer1.org1 -> peer0.org2 -> peer1.org2 -> peer0.org3 -> peer1.org3
    for i in range(1, NUM_OF_ORGS+1):
        for k in range(0, NUM_OF_PEERS):
            url = 'http://%s:9090/api/v1/query' % prometheus_ip_address
            param = 'query= sum(rate(container_cpu_usage_seconds_total{name="peer%s.org%s.example.com"}[1m])) * 100' % (k, i)
            res = req.post(url, params=param)
            data = res.content.decode('utf-8')
            json_data = json.loads(data)
            idx += 1
            # {"node":"peer0.org1.example.com", "cpu_usage": 3.9}
            temp_cpu_info.append(ast.literal_eval(
                '{"node"' + ":" + '"peer' + str(k) + '.org' + str(i) + '.example.com",' + 
                '\"cpu_usage"' + ":" + json_data['data']['result'][0]['value'][1] + '}')
            )
    cpu_info = copy.deepcopy(temp_cpu_info)
    print(cpu_info)

def get_memory_info():
    global mem_info
    temp_mem_info = []
    idx = 0
    prometheus_ip_address = get_prometheus_ip_address()
    for i in range(1, NUM_OF_ORGS+1):
        for k in range(0, NUM_OF_PEERS):
            url = 'http://%s:9090/api/v1/query' % prometheus_ip_address
            param = 'query= container_memory_usage_bytes{name="peer%s.org%s.example.com"} / container_spec_memory_limit_bytes{name="peer%s.org%s.example.com"} * 100' % (k, i, k, i)
            res = req.post(url, params=param)
            data = res.content.decode('utf-8')
            json_data = json.loads(data)
            # {"node":"peer0.org1.example.com", "mem_usage": 4.412}
            temp_mem_info.append(ast.literal_eval(
                '{"node"' + ":" + '"peer' + str(k) + '.org' + str(i) + '.example.com",' + 
                '\"mem_usage"' + ":" + json_data['data']['result'][0]['value'][1] + '}')
            ) 
    mem_info = copy.deepcopy(temp_mem_info)
    print(mem_info)

def get_network_info():
    global net_info
    temp_net_info = []
    idx = 0
    prometheus_ip_address = get_prometheus_ip_address()
    for i in range(1, NUM_OF_ORGS+1):
        for k in range(0, NUM_OF_PEERS):
            url = 'http://%s:9090/api/v1/query' % prometheus_ip_address
            tx_param = 'query= rate(container_network_transmit_bytes_total{name="peer%s.org%s.example.com"}[1m])' % (k, i)
            rx_param = 'query= rate(container_network_receive_bytes_total{name="peer%s.org%s.example.com"}[1m])' % (k, i)
            tx_res = req.post(url, params=tx_param)
            rx_res = req.post(url, params=rx_param)
            tx_data = tx_res.content.decode('utf-8') 
            rx_data = rx_res.content.decode('utf-8')
            tx_json_data = json.loads(tx_data)
            rx_json_data = json.loads(rx_data)
            # {"node":"peer0.org1.example.com", "tx": 1192. "rx": 1156}
            temp_net_info.append(ast.literal_eval(
                '{"node"' + ":" + '"peer' + str(k) + '.org' + str(i) + '.example.com",' + 
                '\"tx"' + ":" + tx_json_data['data']['result'][0]['value'][1] + ',"rx"' + ":" + rx_json_data['data']['result'][0]['value'][1] +'}')
            ) 
    net_info = copy.deepcopy(temp_net_info)
    print(net_info)

# APScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(get_cpu_info, 'interval', seconds=10)
scheduler.add_job(get_memory_info, 'interval', seconds=10)
scheduler.add_job(get_network_info, 'interval', seconds=10)
scheduler.start()

class get_cpu_list(Resource):
    def post(self):
        return cpu_info

class get_mem_list(Resource):
    def post(self):
        return mem_info

class get_net_list(Resource):
    def post(self):
        return net_info

api.add_resource(get_cpu_list, '/get_cpu_list')
api.add_resource(get_mem_list, '/get_mem_list')
api.add_resource(get_net_list, '/get_net_list')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5001) 
