@echo off
echo Multi-LLM 블로그 자동화 시스템 빌드...
echo.

echo [1/3] Frontend 빌드...
call npm run build

echo.
echo [2/3] Electron 앱 빌드...
call npm run electron:build

echo.
echo 빌드 완료!
echo dist 폴더를 확인하세요.
echo.
pause
