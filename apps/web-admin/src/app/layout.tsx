import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import AppShellServer from '@/components/app-shell-server'

export const dynamic = 'force-dynamic'

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Forge MCP Gateway Admin",
  description: "Admin dashboard for Forge MCP Gateway",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} font-sans antialiased`}
      >
        <AppShellServer>{children}</AppShellServer>
      </body>
    </html>
  );
}
