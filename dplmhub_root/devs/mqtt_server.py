from cgi import print_directory
from http import client
from pydoc import cli
from typing import List
from multiprocessing.connection import Client
from urllib.parse import uses_relative
from numpy import deprecate
import paho.mqtt.client as mqtt
from .models import Device
from .serializers import DeviceSerializer
from threading import Lock
import time
from threading import Thread
mqtt_server_adress = "dff8we.stackhero-network.com"
# mqtt_server_adress = "192.168.1.102"
broker_port_unsafe = 1883
broker_port_tls = 8883

class DeviceManager:
    dev_local_adr  = {}  
devman = DeviceManager


class MqttServer():
    '''
    Singleton running parallel to django server
    '''
    _server = None
    _streams = {str: bytearray}
    _streams_mutx = {str: Lock}
    _callbacks = set()
    def __init__(self):
        raise RuntimeError('Call getInstance() instead')

    def streamed(func):
        func()

    @classmethod
    def getInstance(cls):
        if cls._server is None:
            cls._server = cls.__new__(cls)
        return cls._server
    
    def pushStream(self, stream_name, data):
        if (stream_name not in self._streams_mutx):
            self._streams_mutx[stream_name] = Lock()
            
        self._streams_mutx[stream_name].acquire()
        try:
            if stream_name not in self._streams:
                self._streams[stream_name] = bytearray()
            self._streams[stream_name] += bytearray(data)
            print('Push stream ' + stream_name + " "  + str(len(data)))
        finally:
            self._streams_mutx[stream_name].release()

    def pullStream(self, stream_name):        
        if stream_name not in self._streams:
            print('Not found stream')
            return ''
        self._streams_mutx[stream_name].acquire()
        try:
            data = self._streams[stream_name]
            print('Pull stream ' + stream_name + " " + str(len(data)))
            self._streams.pop(stream_name)
        finally:
            self._streams_mutx[stream_name].release()
            return data

    def pull_string_stream(self, stream_name):
        return self.pullStream(stream_name).decode('utf-8')

    def streamMsgCount(self, stream_name):
        if stream_name not in self._streams:
            return 0
        else: 
            return len(self._streams[stream_name])

    def isEmptyStream(self, stream_name):
        return stream_name not in self._streams or self._streams.get(stream_name) == ''

    # The callback for when the _client receives a CONNACK response from the server.
    @staticmethod
    def __on_connect(client, userdata, flags, rc):
        print("Opened mqtt endpoint with result code "+str(rc))
        # _client.subscribe("$SYS/#")
    
    def __setup_callbacks(self):
        self._client.message_callback_add('discovery/registration/#', 
            self.__callback_registration)
        self._client.message_callback_add('config/net/status/#', 
            self.__callback_statusNetwork)
        self._client.message_callback_add('discovery/aad',
            self.__callback_deviceAAD)

    # The callback for when a PUBLISH message is received from the server.
    @staticmethod
    def __on_message(client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))
    @staticmethod
    def __on_disconnect(client, userdata, rc):
        print('Disconnected with result code: ' + str(rc))

    @staticmethod
    def __callback_registration(client, userdata, msg):
        print("MQTT endpoint received: " + msg.topic)
        # remember dev [clientID, user, local_address, last_update_date]
        attributes = msg.payload.decode('utf-8').split(':')

        data = {
            'clientID': attributes[0],
            'user': attributes[1],
            'local_address': attributes[2],
        }
        serializer = DeviceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

    @staticmethod
    def __callback_statusNetwork(client, userdata, msg):
        print("MQTT endpoint received: " + msg.topic)
        print(msg.payload.decode('utf-8'))

    @staticmethod
    def __callback_deviceAAD(client, userdata, msg):
        print("AAD Confirmation not yet implemented")
        #consume and remember aad

    def _makeStreamDigestionF(self, stream_name):
        def __callback_digestStream(client, userdata, msg):
            self.pushStream(stream_name, msg.payload)
        return __callback_digestStream

    def run_mqtt_server(self):
        self._client = mqtt.Client(client_id = "DplmHubServer")
        self._client.enable_logger()
        self._client.on_connect = self.__on_connect
        self._client.on_message = self.__on_message
        self._client.on_disconnect = self.__on_disconnect
        self.__setup_callbacks()
        
        self._client.username_pw_set("server", "GBuNGRiupBbgOHisxz9keuQJPilRyDpk")
        while not self._client.is_connected():
            print("Trying to connect to: " + mqtt_server_adress)
            self._client.connect(mqtt_server_adress, broker_port_unsafe, 60)
            self._client.loop()
        while True:
            self._client.loop()

    def set_network(self, old_ssid: str, old_address: str, ssid: str, password: str):
        """ 
        Old ssid and address are identifiers for a group of devices that need to be reassigned
        """
        self._client.publish(
            "config/net/" + self.parsarg([old_ssid,old_address]),
            self.parsarg([ssid, password]))
    

    def connectStream(self, endpoint, deviceID, stream_name = '########'):
        if stream_name == '########':
            stream_name = endpoint + deviceID
        # print('Subscribing to stream ' + endpoint)
        self._callbacks.add(f'action/read/{endpoint}/{deviceID}')
        self._client.subscribe(f'action/read/{endpoint}/{deviceID}')
        self._client.message_callback_add(f'action/read/{endpoint}/{deviceID}',
            self._makeStreamDigestionF(stream_name))
    # add deletion of a stream
    def disconnectStream(self, endpoint, deviceID):
        self._client.message_callback_remove(f'action/read/{endpoint}/{deviceID}')
        self._callbacks.remove(f'action/read/{endpoint}/{deviceID}')

    def callbackAvailable(self, endpoint, deviceID):
        return f'action/read/{endpoint}/{deviceID}' in self._callbacks

    def dev_update(self, endpoint, deviceID, payload = ""):
        self._client.publish(f'action/update/{endpoint}/{deviceID}', payload)
    
    def dev_put(self, endpoint, deviceID, payload = ""):
        self._client.publish(f'action/put/{endpoint}/{deviceID}', payload)
    
    def dev_read(self, endpoint, deviceID):
        """ Singular read """
        self._client.message_callback_add(f'action/read/{endpoint}/{deviceID}',
            lambda client, userd, msg: print(msg))
        self._client.publish(f'action/update/{endpoint}/{deviceID}')
        def closeCallback():
            time.sleep(1)
            self._client.message_callback_remove(f'action/update/{endpoint}/{deviceID}')
        Thread(closeCallback).run()

    def parsarg(args: List[str]):
        return ':'.join(args)
