const { contextBridge } = require('electron');

// 필요시 메인 프로세스와 통신하는 API 노출
contextBridge.exposeInMainWorld('electronAPI', {
  // 예: 플랫폼 정보
  platform: process.platform,
});
