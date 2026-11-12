@echo off
cd /d D:\My_Projects\PlumbingAutomation
call .venv\Scripts\activate
set CLIENT=test2
set PORT=5001
set NTFY_TOPIC=plumbingpro-RsQ6Qh3znKnZa7h8oXo_2w
set SECRET_KEY=c9bc3d4ff34a6654a858fe2fb54bd4a9906e0c6a68c562b081650f7868f272ed
set ADMIN_PASSWORD=a!b@c#A!B@C#123
set FLASK_DEBUG=1
python app.py
pause