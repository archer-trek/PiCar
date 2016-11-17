#!/usr/bin/env python
# coding: utf-8
from __future__ import (
    unicode_literals,
    print_function,
    absolute_import,
    division,
)
from gpiozero import Motor
import threading
import logging

class MotorGroup(object):

    def __init__(self, *pins):
        self.motors = []
        for pin in pins:
            if len(pin) != 2:
                raise Exception('MotorGroup need pin pairs')
            self.motors.append(Motor(pin[0], pin[1]))

    def forward(self, speed=1):
        for m in self.motors:
            m.forward(speed)

    def backward(self, speed=1):
        for m in self.motors:
            m.backward(speed)

    def reverse(self):
        for m in self.motors:
            m.reverse()

    def stop(self):
        for m in self.motors:
            m.stop()

    @property
    def is_active(self):
        if self.motors:
            return self.motors[0].is_active
        return False

class FourWDCar(object):
    '''
    Four-wheel Drive Car

    Status: stopped, forward, backward, turnleft, turnright
    '''

    STATUS = {
        'stopped': u'停止',
        'forward': u'前进',
        'backward': u'后退',
        'turnleft': u'左转',
        'turnright': u'右转',
    }

    def __init__(self):
        self._status = 'stopped'
        self._dht = None
        self._lock = threading.RLock()

    @property
    def status(self):
        with self._lock:
            return self._status

    @property
    def status_text(self):
        with self._lock:
            return self.STATUS[self._status]

    @status.setter
    def status(self, value):
        if value not in self.STATUS:
            raise Exception(value + ' not valid car status')
        with self._lock:
            if self._status != value:
                logging.info('car status change to %s from %s' % (self._status, value))
                self._status = value
                # todo status changed

    @property
    def info(self):
        v = {
            'status': self.status,
            'humidity': '0.0',
            'temperature': '0.0',
        }
        if self._dht is not None:
            for key, value in self._dht.value.items():
                v[key] = '%.1f' % value
        return v

    def forward(self):
        self.status = 'forward'

    def backward(self):
        self.status = 'backward'

    def stop(self):
        self.status = 'stopped'

    def turnright(self):
        self.status = 'turnright'

    def turnleft(self):
        self.status = 'turnleft'

class PiCar(FourWDCar):

    def __init__(self, left_motor_pins, right_motor_pins, dht_sensor=None):
        super(PiCar, self).__init__()
        self._left_motors = MotorGroup(*left_motor_pins)
        self._right_motors = MotorGroup(*right_motor_pins)
        self._dht = dht_sensor

    def forward(self):
        super(PiCar, self).forward()
        self._left_motors.forward()
        self._right_motors.backward()

    def backward(self):
        super(PiCar, self).backward()
        self._left_motors.backward()
        self._right_motors.forward()

    def stop(self):
        super(PiCar, self).stop()
        self._left_motors.stop()
        self._right_motors.stop()

    def turnright(self):
        super(PiCar, self).turnright()
        self._left_motors.forward()
        self._right_motors.forward()

    def turnleft(self):
        super(PiCar, self).turnleft()
        self._left_motors.backward()
        self._right_motors.backward()

class MockFourWDCar(FourWDCar):

    def __init__(self):
        super(MockFourWDCar, self).__init__()
        from .sensor import DHT
        self._dht = DHT(None, mock=True)
