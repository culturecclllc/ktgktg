@echo off
chcp 65001 >nul
echo ========================================
echo Multi-LLM 블로그 자동화 시스템 설치
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

REM Python 확인
where python >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo.
    echo Python 다운로드: https://www.python.org/
    echo 설치 시 "Add Python to PATH" 옵션을 체크하세요!
    pause
    exit /b 1
)

echo [1/2] Frontend 패키지 설치 중...
echo.
call npm install
if errorlevel 1 (
    echo.
    echo [오류] Frontend 패키지 설치 실패
    echo npm이 제대로 작동하는지 확인하세요.
    pause
    exit /b 1
)
echo.
echo [완료] Frontend 패키지 설치 완료!
echo.

echo [2/2] Backend 패키지 설치 중...
echo.
cd backend
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [오류] Backend 패키지 설치 실패
    echo Python과 pip가 제대로 작동하는지 확인하세요.
    cd ..
    pause
    exit /b 1
)
cd ..
echo.
echo [완료] Backend 패키지 설치 완료!
echo.

echo ========================================
echo 설치 완료!
echo ========================================
echo.
echo 다음 단계:
echo 1. backend/.env 파일을 생성하고 API 키를 설정하세요 (선택사항)
echo 2. start.bat을 실행하여 서버를 시작하세요
echo.
echo 자세한 내용은 설치_가이드.md를 참고하세요.
echo.
pause
