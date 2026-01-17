@echo off
echo Backend 서버 시작 중...
echo.

REM 환경 변수 로드 (선택사항)
if exist .env (
    echo .env 파일을 찾았습니다.
)

python main.py

if errorlevel 1 (
    echo.
    echo 오류: Backend 서버를 시작할 수 없습니다.
    echo 패키지가 설치되어 있는지 확인하세요: install_backend.bat
    pause
)
