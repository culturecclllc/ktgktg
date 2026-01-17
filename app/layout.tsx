import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "YNK 블로그 자동화",
  description: "최고의 블로그 에이전트 - 모든 AI 모델을 통합하여 최고의 컨텐츠 생성",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
