"""
ETCD Helper written in aiohttp
"""
import asyncio
import json
import time

import requests
import base64
import aiohttp


class EtcdHelper(object):
    def __init__(self,ip,port):
        self.ip=ip
        self.port=port
        self.check_version()
        # self.client = Client(ip, port, cert=cert, verify=verify)




    def check_version(self):
        def build_url():
            return "http://{}:{}/version".format(self.ip,self.port)

        # async with aiohttp.ClientSession() as session:
        #     async with session.get(build_url()) as resp:
        #         if resp.status>=300:
        #             raise Exception("Error")
        #         else:
        #             version = await resp.json()["etcdserver"]
        #             print("[*] Etcd Version : {}".format(version))
        #             version_list = version.strip().split('.')
        #             if version_list[0] != "3":
        #                 raise Exception("Etcd Not supported.")
        #             elif int(version_list[1]) <= 3:
        #                 self.api = "v3alpha"
        #             elif int(version_list[1]) >= 4:
        #                 self.api = "v3"
        #             else:
        #                 self.api = "v3"

        resp= requests.get(build_url())
        if resp.status_code>=300:
            resp.raise_for_status()
        else:
            version = resp.json()["etcdserver"]
            print("[*] Etcd Version : {}".format(version))
            version_list=version.strip().split('.')
            if version_list[0]!="3":
                raise Exception("Etcd Not supported.")
            elif int(version_list[1])<=3:
                self.api="v3alpha"
            elif int(version_list[1])>=4:
                self.api="v3"
            else:
                self.api="v3"


    @staticmethod
    def encode(input):
        return str(base64.b64encode(bytes(input,encoding="utf-8")),encoding="utf-8")

    @staticmethod
    def decode(input):
        return str(base64.b64decode(input), encoding="utf-8")


    async def put(self,key,value):
        def build_url():
            return "http://{}:{}/{}/kv/put".format(self.ip,self.port,self.api)

        async with aiohttp.ClientSession() as session:
            async with session.post(build_url(),data='{"key": "%s", "value": "%s"}' % (self.encode(key),self.encode(value))) as resp:
                if resp.status>=300:
                    raise Exception("Error")

        #
        # resp = requests.post(build_url(),data='{"key": "%s", "value": "%s"}' % (self.encode(key),self.encode(value)))
        # if resp.status_code>=300:
        #     resp.raise_for_status()

        # print(self.client.version())
        # self.client.put(key, value)

    async def watch(self,key,func):
        def build_url():
            return "http://{}:{}/{}/watch".format(self.ip,self.port,self.api)

        async with aiohttp.ClientSession() as session:
            async with session.post(build_url(),data='{"create_request": {"key":"%s"} }' % self.encode(key)) as resp:
                if resp.status>=300:
                    raise Exception("Error")
                else:
                    while True:
                        data = await resp.content.readchunk()
                        print(data)
                        json_result= json.loads(data[0])
                        if json_result.get("result") and json_result.get("result").get("events"):
                            for data in json_result.get("result").get("events"):
                                if self.decode(data["kv"]["key"]) == key:
                                    print(self.decode(data["kv"]["value"]))
                                    func(self.decode(data["kv"]["value"]))
                                    break


    async def get(self,key):
        def build_url():
            return "http://{}:{}/{}/kv/range".format(self.ip,self.port,self.api)

        async with aiohttp.ClientSession() as session:
            async with session.post(build_url(),data='{"key": "%s"}' % self.encode(key)) as resp:
                if resp.status>=300:
                    raise Exception("Error")
                else:
                    data = await resp.json()
                    result = data.get('kvs')
                    if not result or len(result)==0:
                        return None
                    else:
                        for value in result:
                            return self.decode(value["value"])

        # resp=requests.post(build_url(),data='{"key": "%s"}' % self.encode(key))
        # if resp.status_code>=300:
        #     resp.raise_for_status()
        # result = resp.json().get('kvs')
        # # result = self.client.range(key).kvs
        # if not result or len(result)==0:
        #     return None
        # else:
        #     for value in result:
        #         return self.decode(value["value"])

async def test():
    while True:
        await sleep_test()
        await asyncio.sleep(0.00001)


async def sleep_test():
    time.sleep(1)

def do_something(value):
    print("Updated: "+ value)




if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    # loop.run_until_complete(EtcdHelper("jp.debug.com",52379).put("foo","foo222"))

    # coro = test()
    # asyncio.ensure_future(coro)
    coro2 = EtcdHelper("jp.debug.com",52379).watch("foo",do_something)
    asyncio.ensure_future(coro2)
    loop.run_forever()
    # loop.run_until_complete(EtcdHelper("jp.debug.com",52379).watch("foo"))
    # etcd=EtcdHelper("jp.debug.com",52379)
    # etcd.put("foo","foo123")
    # print(etcd.get("RouterA"))