module.exports = {
  appId: 'com.multillm.blogautomation',
  productName: 'Multi-LLM 블로그 자동화',
  directories: {
    output: 'dist',
  },
  files: [
    'out/**/*',
    'backend/**/*',
    'electron/**/*',
    'package.json',
    'node_modules/**/*',
  ],
  win: {
    target: 'nsis',
    icon: 'assets/icon.ico',
  },
  nsis: {
    oneClick: false,
    allowToChangeInstallationDirectory: true,
    createDesktopShortcut: true,
    createStartMenuShortcut: true,
  },
  mac: {
    target: 'dmg',
    icon: 'assets/icon.icns',
  },
  linux: {
    target: 'AppImage',
    icon: 'assets/icon.png',
  },
};
