#!/usr/bin/env python
# coding: utf-8
__author__ = 'wzy'
__date__ = '2016-11-12 16:33'

from flask import Flask, render_template
from flask_socketio import SocketIO, Namespace
from car import MockFourWDCar
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s][%(asctime)s][%(module)s] %(message)s')

app = Flask(__name__)
socketio = SocketIO(app)

car = MockFourWDCar()

avalibe_actions = {
    'stop',
    'forward', 'backward',
    'turnright', 'turnleft'
}

@app.route('/')
def index():
    return render_template('index.html', car_state=car.info)

class SocketHandler(Namespace):
    def on_connect(self):
        logging.info('client connected')
        self.emit('car_info', car.info)

    def on_disconnect(self):
        logging.info('client disconnected')

socketio.on_namespace(SocketHandler('/'))

if __name__ == '__main__':
    socketio.run(app)
