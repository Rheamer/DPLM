from cgi import print_directory
from http import client
from pydoc import cli
from typing import List
from multiprocessing.connection import Client
from urllib.parse import uses_relative
import paho.mqtt.client as mqtt
from .models import Device
from threading import Lock
import time
from threading import Thread
from decouple import config
import threading

mqtt_server_address = config("URL_BROKER_NETWORK")
broker_port_unsafe = int(config("BROKER_PORT_UNSAFE"))
broker_port_tls = int(config("BROKER_PORT_TLS"))


# TODO: inherit from gateway interface
class MqttClient:
    """
    Singleton running next to django server
    """
    _server = None
    _callbacks = set()
    _client = None
    _streams = {str: bytearray}
    _streams_mutx = {str: Lock}

    """ Server side callbacks """
    callback_registration = None
    callback_read = None
    callback_status_network = None
    callback_deviceAAD = None

    def __init__(self):
        raise RuntimeError('Call getInstance() instead')

    @classmethod
    def get_instance(cls):
        if cls._server is None:
            cls._server = cls.__new__(cls)
        return cls._server

    """ Internal callbacks """
    @staticmethod
    def __on_connect(client, userdata, flags, rc):
        print("Opened mqtt endpoint with result code "+str(rc))
        # _client.subscribe("$SYS/#")
    
    def __setup_callbacks(self):
        self._client.message_callback_add(
            'discovery/registration/#',
            self.callback_registration)
        self._client.message_callback_add(
            'config/net/status/#',
            self.callback_status_network)
        self._client.message_callback_add(
            'discovery/aad',
            self.callback_deviceAAD)

    # The callback for when a PUBLISH message is received from the server.
    @staticmethod
    def __on_message(client, userdata, msg):
        print(msg.topic+" "+str(msg.payload))

    @staticmethod
    def __on_disconnect(client, userdata, rc):
        print('Disconnected with result code: ' + str(rc))

    """ Utility """
    @staticmethod
    def parsarg(args: List[str]):
        return ':'.join(args)

    """ Public methods """
    def connect(self):
        self._client = mqtt.Client(client_id = config("DJANGO_MQTT_CLIENT_ID"))
        self._client.enable_logger()
        self._client.on_connect = self.__on_connect
        self._client.on_message = self.__on_message
        self._client.on_disconnect = self.__on_disconnect
        self.__setup_callbacks()

        self._client.username_pw_set(
            config("DJANGO_MQTT_USERNAME"),
            config("DJANGO_MQTT_PASSWORD"))

        print("Trying to connect to: " + mqtt_server_address)
        while not self._client.is_connected():
            self._client.connect(mqtt_server_address, broker_port_unsafe, 60)
            self._client.loop()
        self._client.loop_start()

    def set_network(self, old_ssid: str, old_address: str, ssid: str, password: str):
        """
        Old ssid and address are identifiers for a group of devices that need to be reassigned
        """
        self._client.publish(
            "config/net/" + self.parsarg([old_ssid,old_address]),
            self.parsarg([ssid, password]))

    def callbackAvailable(self, endpoint, deviceID):
        return f'action/read/{endpoint}/{deviceID}' in self._callbacks

    """ Action methods """
    def dev_update(self, endpoint, deviceID, payload=""):
        self._client.publish(f'action/update/{endpoint}/{deviceID}', payload)

    def dev_put(self, endpoint, deviceID, payload=""):
        self._client.publish(f'action/put/{endpoint}/{deviceID}', payload)

    def dev_read(self, endpoint, deviceID):
        # Publish request to get a singular response with a value

        def callback_read_close(*args, **kwargs):
            self.callback_read(deviceID=deviceID, endpoint=endpoint, *args, **kwargs)
            self._client.message_callback_remove(
                f'action/read/{endpoint}/{deviceID}')

        self._client.message_callback_add(
            f'action/read/{endpoint}/{deviceID}',
            callback_read_close)
        self._client.publish(f'action/read/{endpoint}/{deviceID}')



    """ Stream related methods """
    def _makeStreamDigestionF(self, stream_name):
        def __callback_digestStream(client, userdata, msg):
            self.push_stream(stream_name, msg.payload)
        return __callback_digestStream

    def push_stream(self, stream_name, data):
        if stream_name not in self._streams_mutx:
            self._streams_mutx[stream_name] = Lock()

        self._streams_mutx[stream_name].acquire()
        try:
            if stream_name not in self._streams:
                self._streams[stream_name] = bytearray()
            self._streams[stream_name] += bytearray(data)
            print('Push stream ' + stream_name + " " + str(len(data)))
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


