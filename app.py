#!/usr/bin/env python
# coding: utf-8
import json
import codecs
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from car import MockFourWDCar, PiCar

app = Flask(__name__)
socketio = SocketIO(app)

def load_car_config():
    with codecs.open('config.json', encoding='utf8') as fp:
        return json.load(fp)['car']

car_config = load_car_config()
if car_config['mock'] is True:
    car = MockFourWDCar()
else:
    car = PiCar(**car_config)

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
