import asyncio
import json

import base64
import aiohttp

from etcd_helper import EtcdHelper


class DataProcessor(object):
    instance=None
    def __init__(self,hostname,port,username,password,xtc_ip):
        self.hostname=hostname
        self.username=username
        self.password=password
        self.etcd=EtcdHelper(hostname,port)
        self.device_list=[]
        self.sid_list={}
        self.node_ip={}
        self.watch_list=[]
        self.calc_list=[]
        self.xtc_ip=xtc_ip
        pass

    @classmethod
    def get_instance(cls,hostname,port,username,password,xtc_ip):
        if cls.instance:
            pass
        else:
            cls.instance = cls(hostname=hostname,port=port,username=username,password=password,xtc_ip=xtc_ip)
        return cls.instance

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

    async def save_to_etcd(self,source,dest,method,seg_list,addition={}):
        key = "{}__{}__{}__{}".format(source,dest,method,json.dumps(addition))
        value = json.dumps(seg_list)
        await self.etcd.put(key,value)

    def check_if_watched(self,source,dest,method,addition):
        for calc in self.calc_list:
            if calc["source"]==source and calc["dest"] == dest and calc["method"] == method and calc["addition"] ==addition:
                return True
        return False

    async def get_calc(self,source,dest,method,addition={}):
        def add_to_watch_list(sids):
            record = [self.sid_list[source],self.sid_list[dest]]
            record.extend(sids)
            self.calc_list.append({
                "source":source,
                "dest":dest,
                "method":method,
                "addition":addition,
                "sids":record
            })

        # result = await self.etcd.get("{}__{}__{}__{}".format(source,dest,method,json.dumps(addition)))
        watched = self.check_if_watched(source, dest, method, addition)

        # Debug
        # watched = False

        # if result:
        #     result=json.loads(result)
        # else:
        # result = await self.calc(source,dest,method,addition)
        if not watched:
            result = await self.calc(source, dest, method, addition)
            add_to_watch_list(result)
        else:
            result = await self.etcd.get("{}__{}__{}__{}".format(source, dest, method, json.dumps(addition)))

        return result


    async def calc(self,source,dest,method,addition={}):
        assert method in ['igp', 'te', 'latency']
        assert source in self.device_list
        assert dest in self.device_list
        self.pc = PathCalculator(ip=self.xtc_ip,username=self.username,password=self.password,node_table=self.node_ip)
        result = await self.pc.compute(source,dest,method)
        sid_path=[]
        if result:
            for node in result:
                sid_path.append(self.sid_list[node])
        await self.save_to_etcd(source,dest,method,sid_path,addition)
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

    async def start_watch(self):
        await self.get_devices()
        await self.get_node_ip()
        await self.get_sids()
        while True:
            self.watch_sid()
            await asyncio.sleep(120)


    def watch_sid(self):
        for device in self.device_list:
            if device not in self.watch_list:
                coro = self.etcd.watch(device,self.update_path)
                asyncio.ensure_future(coro)
                self.watch_list.append(device)

    async def update_path(self,device):
        def update_watch(obj,sids):
            obj["sids"]=sids


        await self.get_sids()
        for calc in self.calc_list:
            if self.sid_list[device] in calc["sids"]:
                sids = await self.calc(calc["source"],calc["dest"],calc["method"],calc["addition"])
                update_watch(calc,sids)

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
