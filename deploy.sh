#!/usr/bin/env bash

set -e

rsync -r -v --exclude=__pycache__ ./* pi:PiCar/
ssh pi "sudo supervisorctl restart car"