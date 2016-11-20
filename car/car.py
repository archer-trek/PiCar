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
from .log import get_logger
try:
    from queue import Queue
    from queue import Full
except ImportError:
    from Queue import Queue
    from Queue import Full

logger = get_logger('car')

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

    _STATUS = {
        'stopped': u'停止',
        'forward': u'前进',
        'backward': u'后退',
        'turnleft': u'左转',
        'turnright': u'右转',
    }

    _AVALIBE_ACTIONS = {
        'stop',
        'forward', 'backward',
        'turnright', 'turnleft', 'turnstop'
    }

    def __init__(self):
        self._status = 'stopped'
        self._stashed_status = None
        self._lock = threading.RLock()

        self.when_changed = None
        self._queue = Queue(maxsize=1)
        self._consumer = threading.Thread(target=self._consume)
        self._consumer.daemon = True
        self._consumer.start()

    def _consume(self):
        while True:
            self._queue.get()
            if self.when_changed is not None:
                self.when_changed(self.info)
            self._queue.task_done()

    def _push_status(self, status):
        self._stashed_status = status

    def _pop_status(self):
        status = self._stashed_status
        self._stashed_status = None
        return status

    def _peek_status(self):
        return self._stashed_status

    @property
    def status(self):
        with self._lock:
            return self._status

    @property
    def status_text(self):
        with self._lock:
            return self._STATUS[self._status]

    @status.setter
    def status(self, value):
        if value not in self._STATUS:
            raise Exception(value + ' not valid car status')
        with self._lock:
            if self._status != value:
                logger.info('car status changed, %10s --> %-10s' % (self._status, value))
                self._status = value
                self._nofity_change()

    def _nofity_change(self):
        try:
            self._queue.put_nowait(True)
        except Full:
            pass

    @property
    def info(self):
        return {
            'status': self.status,
            'status_text': self.status_text,
            'humidity': '0.0',
            'temperature': '0.0',
        }

    def forward(self):
        self.status = 'forward'
        self._push_status('forward')

    def backward(self):
        self.status = 'backward'
        self._push_status('backward')

    def stop(self):
        self.status = 'stopped'
        self._push_status('stopped')

    def turnright(self):
        self._push_status(self.status)
        self.status = 'turnright'

    def turnleft(self):
        self._push_status(self.status)
        self.status = 'turnleft'

    def turnstop(self):
        status = self._pop_status()
        if status == 'forward':
            self.forward()
        elif status == 'backward':
            self.backward()
        elif status == 'stopped':
            self.stop()

    def do_action(self, action):
        if action in self._AVALIBE_ACTIONS:
            getattr(self, action)()

class PiCar(FourWDCar):

    def __init__(self, left_motor_pins, right_motor_pins, dht_sensor_pin=None, **kwargs):
        super(PiCar, self).__init__()
        self._left_motors = MotorGroup(*left_motor_pins)
        self._right_motors = MotorGroup(*right_motor_pins)

        self._humidity = 0.0
        self._temperature = 0.0

        if dht_sensor_pin is not None:
            from .sensor import DHT
            self._dht = DHT(dht_sensor_pin)

            def changed(h, t):
                self._humidity = h
                self._temperature = t
                self._nofity_change()
            self._dht.when_changed = changed

    @property
    def info(self):
        v = super(PiCar, self).info
        v['humidity'] = '%.1f' % self._humidity
        v['temperature'] = '%.1f' % self._temperature
        return v

    def forward(self):
        super(PiCar, self).forward()
        self._left_motors.forward()
        self._right_motors.forward()

    def backward(self):
        super(PiCar, self).backward()
        self._left_motors.backward()
        self._right_motors.backward()

    def stop(self):
        super(PiCar, self).stop()
        self._left_motors.stop()
        self._right_motors.stop()

    def turnright(self):
        super(PiCar, self).turnright()
        if self._peek_status() == 'backward':
            self._left_motors.backward()
            self._right_motors.forward()
        else:
            self._left_motors.forward()
            self._right_motors.backward()

    def turnleft(self):
        super(PiCar, self).turnleft()
        if self._peek_status() == 'backward':
            self._left_motors.forward()
            self._right_motors.backward()
        else:
            self._left_motors.backward()
            self._right_motors.forward()

class MockFourWDCar(FourWDCar):

    def __init__(self):
        super(MockFourWDCar, self).__init__()
        self._humidity = 0.0
        self._temperature = 0.0

        from .sensor import DHT
        self._dht = DHT(None, mock=True)

        def changed(h, t):
            self._humidity = h
            self._temperature = t
            self._nofity_change()
        self._dht.when_changed = changed

    @property
    def info(self):
        v = super(MockFourWDCar, self).info
        v['humidity'] = '%.1f' % self._humidity
        v['temperature'] = '%.1f' % self._temperature
        return v