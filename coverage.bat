@echo off
call .venv\Scripts\activate.bat
set PYTHONPATH=.
python -m coverage run -m unittest discover -s tests
python -m coverage report
python -m coverage html