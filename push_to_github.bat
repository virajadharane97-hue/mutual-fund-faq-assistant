@echo off
echo Configuring Git...
git config --global user.email "viraj@example.com"
git config --global user.name "Viraj"

echo Adding files...
git add .

echo Committing...
git commit -m "Initial commit: Mutual Fund FAQ Assistant"

echo Pushing to GitHub...
git branch -M main
git push -u origin main --force

echo.
echo All done! Your code has been pushed to GitHub.
pause
