@echo off
pyinstaller -F .\B.py .\Client.py ..\utils\utils.py
pyinstaller -F .\C.py .\Client.py ..\utils\utils.py
pyinstaller -F .\D.py .\Client.py ..\utils\utils.py
pyinstaller -F .\E.py .\Client.py ..\utils\utils.py
pyinstaller -F .\Server.py ..\utils\utils.py