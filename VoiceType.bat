@echo off
cd /d "%~dp0"
set "vbs=%temp%\voicetype_%random%.vbs"
echo Set ws = CreateObject("Wscript.Shell") > "%vbs%"
echo ws.CurrentDirectory = "%~dp0" >> "%vbs%"
echo ws.Run "C:\Users\G\AppData\Local\Programs\Python\Python311\python.exe voice_to_text.py", 0, False >> "%vbs%"
wscript.exe "%vbs%"
del "%vbs%"
