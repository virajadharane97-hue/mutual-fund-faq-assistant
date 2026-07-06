@echo off
echo ===================================================
echo   Mutual Fund FAQ Assistant - Auto Setup Launcher
echo ===================================================
echo.
echo WARNING: Make sure you have paused OneDrive syncing before running this!
echo If you haven't, close this window, pause OneDrive, and double-click this file again.
echo.
pause

echo.
echo [Step 1] Installing required packages...
pip install -r requirements.txt

echo.
echo [Step 2] Running data ingestion pipeline (Downloading models & scraping data)...
python retrieval/vector_store.py

echo.
echo [Step 3] Starting the application...
python -m streamlit run ui/app.py

pause
