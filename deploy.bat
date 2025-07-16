@echo off
echo "# myalgoserver" >> README.md
git init
git add .
git commit -m "logout added"
git branch -M main
REM git remote add origin https://github.com/mosinDataBase/myalgoserver.git
git push -u origin main

echo === ✅ Deployment Complete ===
pause
