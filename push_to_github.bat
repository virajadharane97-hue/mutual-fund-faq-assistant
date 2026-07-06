@echo off
echo 1. Initializing Git...
git init

echo 2. Setting GitHub Remote...
git remote add origin https://github.com/virajadharane97-hue/mutual-fund-faq-assistant.git
git remote set-url origin https://github.com/virajadharane97-hue/mutual-fund-faq-assistant.git

echo 3. Configuring Git Identity...
git config --global user.email "viraj@example.com"
git config --global user.name "Viraj"

echo 4. Adding files...
git add .

echo 5. Committing...
git commit -m "Initial commit: Mutual Fund FAQ Assistant"

echo 6. Pushing to GitHub...
git branch -M main
git push -u origin main --force

echo.
echo =========================================
echo PLEASE READ THE TEXT ABOVE FOR ANY ERRORS
echo =========================================
pause
