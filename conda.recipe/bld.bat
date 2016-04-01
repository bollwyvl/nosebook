"%PYTHON%" -m flake8 setup.py nosebook && "%PYTHON%" setup.py install && if errorlevel 1 exit 1
