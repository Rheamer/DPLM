import functools
from typing import List
import paho.mqtt.client as mqtt
from decouple import config

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

    def post_callback_remove(topic, client):
        def inner(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                func(*args, **kwargs)
                client.


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
        self._client.message_callback_add(
            "config/net/status/"+self.parsarg([old_ssid,old_address]),
        )
        self._client.publish(
            "config/net/" + self.parsarg([old_ssid,old_address]),
            self.parsarg([ssid, password]))

    """ Action methods """
    def dev_update(self, endpoint, deviceID, payload=""):
        self._client.publish(f'action/update/{endpoint}/{deviceID}', payload)

    def dev_put(self, endpoint, deviceID, payload=""):
        self._client.publish(f'action/put/{endpoint}/{deviceID}', payload)

    def dev_read(self, endpoint, clientID):
        # Publish request to get a singular response with a value

        def callback_read_close(*args, **kwargs):
            self.callback_read(deviceID=clientID, endpoint=endpoint, *args, **kwargs)
            self._client.message_callback_remove(
                f'action/read/{endpoint}/{clientID}')

        self._client.message_callback_add(
            f'action/read/{endpoint}/{clientID}',
            callback_read_close)
        self._client.publish(f'action/read/{endpoint}/{clientID}')

    def connect_stream(
        self,
        endpoint: str,
        clientID: str,
        # TODO: define callable arguments
        digest_stream: callable
    ):
        self._client.message_callback_add(
            f'action/read/{endpoint}/{clientID}',
            digest_stream)

    def disconnect_stream(
            self,
            endpoint: str,
            clientID: str
    ):
        self._client.message_callback_remove(f'action/read/{endpoint}/{clientID}')