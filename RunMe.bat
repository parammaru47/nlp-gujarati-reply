@echo off
color 0A
TITLE Gujarati Smart Reply Engine Deployment

echo ==================================================
echo      GUJARATI SMART REPLY - ONE CLICK LAUNCHER
echo ==================================================
echo.

echo [1/3] Checking and installing Python dependencies...
python -m pip install -q flask flask-cors scikit-learn gensim pandas numpy joblib

echo.
echo [2/3] Launching Chrome with Extension securely loaded...
start chrome --load-extension="%~dp0extension" https://web.whatsapp.com

echo.
echo [3/3] Booting NLP Brain... Wait for "Running on http://127.0.0.1:5000"
echo --------------------------------------------------
echo IMPORTANT: KEEP THIS WINDOW OPEN WHILE CHATTING!
echo --------------------------------------------------
echo.
python nlp/api.py

pause
