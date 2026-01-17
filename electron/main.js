const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    icon: path.join(__dirname, '../assets/icon.png'), // 아이콘 경로 (선택사항)
  });

  // 개발 모드에서는 Next.js 개발 서버 사용
  if (process.env.NODE_ENV === 'development') {
    // Next.js 개발 서버 알림 비활성화
    mainWindow.webContents.on('did-finish-load', () => {
      // 페이지 로드 후 즉시 제거
      mainWindow.webContents.executeJavaScript(`
        // 개발 서버 알림 제거
        const removeIndicator = () => {
          const indicator = document.getElementById('devtools-indicator');
          if (indicator) {
            indicator.remove();
          }
          const toasts = document.querySelectorAll('[data-nextjs-toast]');
          toasts.forEach(toast => toast.remove());
        };
        
        // 즉시 실행
        removeIndicator();
        
        // DOM 변경 감지하여 계속 제거
        const observer = new MutationObserver(() => {
          removeIndicator();
        });
        
        observer.observe(document.body, {
          childList: true,
          subtree: true
        });
        
        // CSS로도 숨기기
        const style = document.createElement('style');
        style.textContent = \`
          #devtools-indicator,
          [data-nextjs-toast],
          [data-nextjs-dialog],
          [id^="__next"],
          [data-next-badge-root] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
          }
        \`;
        document.head.appendChild(style);
      `);
      
      // 페이지 내비게이션 후에도 제거
      mainWindow.webContents.on('dom-ready', () => {
        mainWindow.webContents.executeJavaScript(`
          const indicator = document.getElementById('devtools-indicator');
          if (indicator) indicator.remove();
          document.querySelectorAll('[data-nextjs-toast]').forEach(el => el.remove());
        `);
      });
    });
    mainWindow.loadURL('http://localhost:3000');
    // 개발자 도구 자동 열기 비활성화 (선택사항)
    // mainWindow.webContents.openDevTools();
  } else {
    // 프로덕션 모드에서는 빌드된 파일 사용
    mainWindow.loadFile(path.join(__dirname, '../out/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startBackend() {
  const backendPath = path.join(__dirname, '../backend');
  const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
  
  backendProcess = spawn(pythonPath, ['main.py'], {
    cwd: backendPath,
    env: {
      ...process.env,
      PYTHONUNBUFFERED: '1',
    },
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`Backend Error: ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });
}

app.whenReady().then(() => {
  startBackend();
  
  // 백엔드가 시작될 때까지 잠시 대기
  setTimeout(() => {
    createWindow();
  }, 2000);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});
