@echo off
chcp 65001 >nul
echo ========================================
echo Frontend 패키지 설치
echo ========================================
echo.

REM Node.js 확인
where node >nul 2>&1
if errorlevel 1 (
    echo [오류] Node.js가 설치되어 있지 않습니다.
    echo.
    echo Node.js 다운로드: https://nodejs.org/
    echo 설치 후 이 스크립트를 다시 실행하세요.
    pause
    exit /b 1
)

echo 패키지 설치 중...
echo.
call npm install

if errorlevel 1 (
    echo.
    echo [오류] 패키지 설치 실패!
    echo Node.js와 npm이 제대로 작동하는지 확인하세요.
    pause
    exit /b 1
)

echo.
echo [완료] Frontend 패키지 설치 완료!
echo.
pause
