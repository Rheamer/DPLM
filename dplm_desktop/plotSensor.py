# This Python file uses the following encoding: utf-8

import paho.mqtt.client as mqtt
import matplotlib.pyplot as plt
import matplotlib.figure as fig
from matplotlib.animation import FuncAnimation, TimedAnimation
from matplotlib.lines import Line2D
import numpy as np, collections

class RealTimePlotter(TimedAnimation):
    def __init__(self):
        self.addedData = []
        self.xlen = 400
        self.data = np.linspace(0, self.xlen - 1, self.xlen)
        self.y = (self.data * 0.0)
        self.fig = plt.figure(figsize=(12, 6), facecolor='#DEDEDE')
        self.ax1 = self.fig.add_subplot(111)
        self.ax1.set_ylabel('raw data')
        self.line1 = Line2D([], [], color='blue', linewidth=0.5)
        self.line1_tail = Line2D([], [], color='red', linewidth=0.5)
        self.line1_head = Line2D([], [], color='red', marker='o', markeredgecolor='r', linewidth= 0.5)
        self.ax1.add_line(self.line1)
        self.ax1.add_line(self.line1_tail)
        self.ax1.add_line(self.line1_head)
        self.ax1.set_xlim(0, self.xlen - 1)
        self.ax1.set_ylim(0, 250)
        TimedAnimation.__init__(self, self.fig, interval=20, blit=True)

    in_frame_data_gather_func = None

    def add_data(self, value):
        self.addedData.append(value)
        return

    def new_frame_seq(self):
        return iter(range(self.data.size))

    def _init_draw(self):
        lines = [self.line1, self.line1_tail, self.line1_head]
        for l in lines:
            l.set_data([], [])
        return



    def _draw_frame(self, framedata):
        self.in_frame_data_gather_func()
        margin = 2
        while(len(self.addedData) > 0):
            self.y = np.roll(self.y, -1)
            self.y[-1] = self.addedData[0]
            del(self.addedData[0])

        self.line1.set_data(
            self.data[ 0 : self.data.size - margin ],
            self.y[ 0 : self.data.size - margin ])
        self.line1_tail.set_data(
            np.append(self.data[-10:-1 - margin], self.data[-1 - margin]),
            np.append(self.y[-10:-1 - margin], self.y[-1 - margin]))
        self.line1_head.set_data(
            self.data[-1 - margin],
            self.y[-1 - margin])
        self._drawn_artists = [self.line1, self.line1_tail, self.line1_head]
        return


class MqttStreamPlotter:

    def __init__(self, clientID):
        self.wlen = 5
        self.client = mqtt.Client(client_id=clientID)
        self.client.username_pw_set(username='plotter', password='NqEnK7WegmSLIE66f2L7aedtgjAl352b')
        self.client.on_message = self.on_message
        self.rtplot = RealTimePlotter()
        def in_frame_action():
            self.client.loop()
        self.rtplot.in_frame_data_gather_func = in_frame_action

    def on_message(self, client, userdata, msg):
        arr_data = np.array(msg.payload).tolist()
        median_data = np.zeros(int(len(msg.payload)/self.wlen))
        for i in range(self.wlen-1, len(msg.payload), self.wlen):
            average_window = []
            for j in range(self.wlen):
                average_window.append(arr_data[i-j])
            median_data[int(i/self.wlen)]=np.average(average_window)
        for v in median_data:
            self.rtplot.add_data(v)


    def plot(self, topic, host, port=1883):
        port = int(port)
        self.client.connect(host, port)
        self.client.subscribe(topic)
        if self.client.is_connected():
            print('No connection')
            print(topic, host, port)
            return -1
        plt.show()


plotter = MqttStreamPlotter(clientID='admin')
plotter.plot('action/read/stream/ESP32', 'dff8we.stackhero-network.com')
