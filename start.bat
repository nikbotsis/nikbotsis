@echo off
cd /d D:\My_Projects\PlumbingAutomation
call .venv\Scripts\activate
set NTFY_TOPIC=plumbingpro-RsQ6Qh3znKnZa7h8oXo_2w
set SECRET_KEY=3762bcb90b590ca10768b8b69cf90ea3309dc35d2ac7f69fdf14ea785a0ecb64
set ADMIN_PASSWORD=a!b@c#A!B@C#123
set FLASK_DEBUG=1
python app.py
pause