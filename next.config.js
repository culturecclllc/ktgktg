/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  // Electron을 위한 설정
  basePath: process.env.NODE_ENV === 'production' ? '' : '',
  // 개발 서버 알림 비활성화
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },
  // Next.js 개발 도구 배지 비활성화
  devIndicators: false,
}

module.exports = nextConfig
