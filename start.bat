@echo off
echo Multi-LLM 블로그 자동화 시스템 시작...
echo.

REM 패키지 설치 확인
if not exist "node_modules\" (
    echo Frontend 패키지가 설치되지 않았습니다.
    echo install_frontend.bat을 먼저 실행해주세요.
    pause
    exit /b 1
)

if not exist "backend\venv\" (
    echo Backend 패키지 확인 중...
    python -c "import fastapi" 2>nul
    if errorlevel 1 (
        echo Backend 패키지가 설치되지 않았습니다.
        echo install_backend.bat을 먼저 실행해주세요.
        pause
        exit /b 1
    )
)

echo [1/2] Backend 서버 시작...
start cmd /k "cd backend && python main.py"

timeout /t 3 /nobreak > nul

echo [2/2] Frontend 서버 시작...
start cmd /k "cd . && npm run dev"

echo.
echo 서버가 시작되었습니다!
echo Frontend: http://localhost:3000
echo Backend: http://localhost:8000
echo.
echo 서버를 종료하려면 각 창을 닫으세요.
echo.
pause
