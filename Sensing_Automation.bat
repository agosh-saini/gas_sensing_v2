@echo off
if not exist logs (
    mkdir logs
)
set timestamp=%date:~-4,4%-%date:~-10,2%-%date:~-7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%
set timestamp=%timestamp: =0%
python your_script.py > logs\log_%timestamp%.txt 2>&1
