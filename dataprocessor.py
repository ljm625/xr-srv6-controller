import asyncio
import json

import base64
import aiohttp

from etcd_helper import EtcdHelper


class DataProcessor(object):
    def __init__(self,hostname,port,username,password):
        self.hostname=hostname
        self.username=username
        self.password=password
        self.etcd=EtcdHelper(hostname,port)
        self.device_list=[]
        self.sid_list={}
        self.node_ip={}
        pass

    async def get_devices(self):
        json_list = await self.etcd.get("nodes")
        try:
            self.device_list = json.loads(json_list)
            return self.device_list
        except:
            raise Exception("Failed to get device list")


    async def get_node_ip(self):
        json_list = await self.etcd.get("node_ip")
        try:
            self.node_ip = json.loads(json_list)
        except:
            raise Exception("Failed to get node ip")



    async def calc(self,source,dest,method):
        await self.get_devices()
        await self.get_node_ip()
        await self.get_sids()
        assert method in ['igp', 'te', 'latency']
        assert source in self.device_list
        assert dest in self.device_list
        self.pc = PathCalculator(ip=self.hostname,username=self.username,password=self.password,node_table=self.node_ip)
        result = await self.pc.compute(source,dest,method)
        sid_path=[]
        if result:
            for node in result:
                sid_path.append(self.sid_list[node])
        return sid_path


    async def get_sids(self):
        def get_end_sid(result):
            for sid in result:
                if sid['name'] == 'end-with-psp':
                    return sid['sid']
            return None

        for device in self.device_list:
            result = await self.etcd.get(device)
            self.sid_list[device] = get_end_sid(json.loads(result))



class PathCalculator(object):
    def __init__(self,ip,username,password,node_table):
        self.ip=ip
        self.username=username
        self.password=password
        self.node_table=node_table
        self.ip_table=dict(zip(self.node_table.values(),self.node_table.keys()))

        pass

    def _build_url(self):
        return "http://{}:8080/lsp/compute/simple".format(self.ip)

    async def compute(self,source,dest,method):
        def build_payload():
            params= {
                "type":"sr",
                "source":self.node_table[source],
                "destination":self.node_table[dest],
                "protected":1
            }
            assert method in ['igp','te','latency']
            params['metric-{}'.format(method)]=1
            return params
        auth = aiohttp.BasicAuth(login=self.username, password=self.password)
        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(self._build_url(),params=build_payload()) as resp:
                if resp.status>=300:
                    raise Exception("Error")
                else:
                    result = await resp.text()
                    json_output=json.loads(result)
                    return self._calculate_path(json_output)

        # response = requests.get(self._build_url(),params=build_payload(),auth=(self.username, self.password))
        # if response.status_code!=200:
        #     response.raise_for_status()
        # return self._calculate_path(response.json())

    def _calculate_path(self,json):
        jumps=[]
        for data in json["data_gpbkv"][0]["fields"]:
            jumps.append(self.ip_table[data['fields'][2]["string_value"]])
        return jumps

class Translator(object):
    def __init__(self,node_sid):
        self.node_sid=node_sid
    def translate(self,node):
        return self.node_sid[node]
