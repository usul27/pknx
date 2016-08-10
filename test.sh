#!/bin/sh
cd `dirname $0`
find . -name __pycache__ | xargs rm -rf
pylint knxip/*.py
PYTHONPATH=. py.test

