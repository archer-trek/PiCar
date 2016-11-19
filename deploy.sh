#!/usr/bin/env bash

set -e

rsync -r -v --exclude=__pycache__ --exclude=config.json ./* pi:PiCar/
ssh pi "sudo supervisorctl restart car"