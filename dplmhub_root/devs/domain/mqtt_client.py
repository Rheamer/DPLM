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
    _client = None

    """ Server side callbacks """
    @staticmethod
    def dummy_callback(*args, **kwargs):
        raise RuntimeError('Callback unimplemented!')
    callbacks: [str, callable] = {
        'registration': dummy_callback,
        'read': dummy_callback,
        'status_network': dummy_callback,
        'callback_deviceAAD': dummy_callback,
    }

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
        self._add_callback(
            'discovery/registration',
            self.callbacks['registration'])

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

    def _add_callback(self, topic: str, callback: callable):
        self._client.subscribe(topic)
        self._client.message_callback_add(topic, callback)

    def _remove_callback(self, topic: str):
        self._client.unsubscribe(topic)
        self._client.message_callback_remove(topic)

    """ Public methods """
    def connect(self):
        self._client = mqtt.Client(client_id=config("DJANGO_MQTT_CLIENT_ID"))
        self._client.enable_logger()

        self._client.username_pw_set(
            config("DJANGO_MQTT_USERNAME"),
            config("DJANGO_MQTT_PASSWORD"))

        self._client.on_connect = self.__on_connect
        self._client.on_message = self.__on_message
        self._client.on_disconnect = self.__on_disconnect

        print("Trying to connect to: " + mqtt_server_address)
        while not self._client.is_connected():
            self._client.connect(mqtt_server_address, broker_port_unsafe, 60)
            self._client.loop()

        self.__setup_callbacks()
        self._client.loop_start()

    def set_network(
        self, clientID,
        old_ssid: str,
        old_address: str,
        ssid: str,
        password: str
    ):
        def callback_switch_close(*args):
            self.callbacks['status_network'](
                *args,
                clientID=clientID,
                new_ssid=ssid,
                old_ssid=old_ssid)
            self._remove_callback(
                "config/net/status/"+self.parsarg([old_ssid, old_address]))

        self._add_callback(
            "config/net/status/"+self.parsarg([old_ssid, old_address]),
            callback_switch_close
        )
        self._client.publish(
            "config/net/" + self.parsarg([old_ssid, old_address]),
            self.parsarg([ssid, password]))

    """ Action methods """
    def dev_update(self, endpoint, clientID, payload: bytes):
        self._client.publish(f'action/update/{endpoint}/{clientID}', payload)

    def dev_put(self, endpoint, clientID, payload: bytes):
        self._client.publish(f'action/put/{endpoint}/{clientID}', payload)

    def dev_read(self, endpoint, clientID):
        # Publish request to get a singular response with a value

        def callback_read_close(*args, **kwargs):
            self.callbacks['read'](*args, clientID=clientID, endpoint=endpoint)
            self._remove_callback(
                f'action/read/{endpoint}/{clientID}')

        self._add_callback(
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
        self._add_callback(
            f'action/read/{endpoint}/{clientID}',
            digest_stream)

    def disconnect_stream(
            self,
            endpoint: str,
            clientID: str
    ):
        self._remove_callback(f'action/read/{endpoint}/{clientID}')
