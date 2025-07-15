@echo off
echo "# MyAlgo" >> README.md
echo "# myalgoserver" >> README.md
git init
git add README.md
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/mosinDataBase/myalgoserver.git
git push -u origin main

echo === ✅ Deployment Complete ===
pause
