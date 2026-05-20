@echo off
title FIBOTREND Agent
:: Di chuyển đến thư mục chứa code của bạn
:: cd /d "C:\BotCoin\BotTrade_FiboTrend"

:: Kiểm tra và cài đặt thư viện nếu thiếu
:: echo Checking dependencies...
:: pip install -r requirements.txt

:: Chạy Agent
echo Starting Agent...
python main.py

pause