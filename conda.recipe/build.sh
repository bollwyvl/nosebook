#!/bin/bash
flake8 setup.py nosebook
"${PYTHON}" setup.py install
