@echo off
chcp 65001 >nul
echo ========================================
echo Backend 패키지 설치
echo ========================================
echo.

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

cd backend
echo pip 업그레이드 중...
python -m pip install --upgrade pip
echo.
echo 패키지 설치 중...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [오류] 패키지 설치 실패!
    echo Python과 pip가 제대로 작동하는지 확인하세요.
    cd ..
    pause
    exit /b 1
)

cd ..
echo.
echo [완료] Backend 패키지 설치 완료!
echo.
pause
