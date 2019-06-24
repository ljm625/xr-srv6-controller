import asyncio
import getopt
import sys
import traceback

import tornado.ioloop
import tornado.web
import json
from dataprocessor import DataProcessor

username = password = etcd_ip = etcd_port = xtc_ip = None


class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', ' GET, POST, PUT, DELETE, OPTIONS')
        self.set_header("Access-Control-Allow-Headers", "*")

    def options(self, *args, **kwargs):
        # no body
        self.set_status(204)
        self.finish()


class DeviceListHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dp = DataProcessor.get_instance(hostname=etcd_ip, port=etcd_port, username=username, password=password,xtc_ip=xtc_ip)
    async def get(self):
        try:
            device_list = await self._dp.get_devices()
            self.write(json.dumps(device_list))
        except Exception as e:
            self.write(json.dumps({"error": str(e)}))
        return




class RouterCalcHandler(BaseHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dp = DataProcessor.get_instance(hostname=etcd_ip, port=etcd_port, username=username, password=password,xtc_ip=xtc_ip)

    async def get(self):
        pass

    async def post(self):
        try:
            data = json.loads(self.request.body)
            assert type(data.get("source")) == str
            assert type(data.get("dest")) == str
            assert data.get("method") in ("te","igp","latency")
        except Exception as e:
            self.write(json.dumps({"error": "params are not valid"}))
            return
        try:
            result = await self._dp.get_calc(data.get("source"),data.get("dest"),data.get("method"))
            self.write(json.dumps({"result":"success", "sid_list":result}))
        except Exception as e:
            traceback.print_exc()
            self.write(json.dumps({"error": str(e)}))





if __name__ == "__main__":

    opts, args = getopt.getopt(sys.argv[1:], '-h:-u:-p:-i:-e:-x:', ['help', 'username=', 'password=', 'etcd-ip=', 'etcd-port=', 'xtc-ip='])
    for opt_name, opt_value in opts:
        if opt_name in ('-h', '--help'):
            print(
                "[*] Help: Please enter username, password, Etcd IP, Etcd Port in parameters. Example: \n python main.py -u cisco -p cisco -i 127.0.0.1 -e 2379")
            exit()
        # if opt_name in ('-d', '--device-name'):
        #     device_name= opt_value
        #     print("[*] Device name is {}".format(device_name))
        if opt_name in ('-u', '--username'):
            username = opt_value
            print("[*] Username is {}".format(username))
            # do something
        if opt_name in ('-p', '--password'):
            password = opt_value
            print("[*] Password is {}".format(password))
        if opt_name in ('-i', '--etcd-ip'):
            etcd_ip = opt_value
            print("[*] Etcd IP is {}".format(etcd_ip))
        if opt_name in ('-e', '--etcd-port'):
            etcd_port = int(opt_value)
            print("[*] Etcd Port is {}".format(etcd_port))
        if opt_name in ('-x', '--xtc-ip'):
            xtc_ip = opt_value
            print("[*] XTC IP is {}".format(xtc_ip))

    if None in [username, password, etcd_ip, etcd_port,xtc_ip]:
        print(
            "[*] Help: Please enter username, password, Etcd IP, Etcd Port in parameters. Example: \n python main.py -u cisco -p cisco -e 127.0.0.1 -ep 2379")
        exit()

    application = tornado.web.Application([
        (r"/api/v1/devices", DeviceListHandler),
        (r"/api/v1/calculate", RouterCalcHandler)
    ])
    application.listen(9888)
    loop = asyncio.get_event_loop()
    dp = DataProcessor.get_instance(hostname=etcd_ip, port=etcd_port, username=username, password=password, xtc_ip=xtc_ip)
    asyncio.ensure_future(dp.start_watch())
    loop.run_forever()

    # tornado.ioloop.IOLoop.current().start()



