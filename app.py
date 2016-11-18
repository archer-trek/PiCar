#!/usr/bin/env python
# coding: utf-8
__author__ = 'wzy'
__date__ = '2016-11-12 16:33'

import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from car import MockFourWDCar

# import logging
# logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
socketio = SocketIO(app)

car = MockFourWDCar()

@app.route('/')
def index():
    return render_template('index.html', car_state=car.info)

@socketio.on('connect')
def on_connect():
    emit('car_info', car.info)

@socketio.on('disconnect')
def on_disconnect():
    pass

@socketio.on('car_action')
def on_car_action(action):
    car.do_action(action)

car.when_changed = lambda v: eventlet.spawn_n(socketio.emit, 'car_info', v)

if __name__ == '__main__':
    socketio.run(app)
