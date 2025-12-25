import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import ErrorBoundary from '../components/ErrorBoundary';
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "VM KULA 2026 - AI-drevne VM-spådommer",
  description: "AI-drevne spådommer for FIFA Fotball-VM 2026 med Gemini AI",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const messages = await getMessages();

  return (
    <html lang="nb">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ErrorBoundary>
          <NextIntlClientProvider messages={messages}>
            {children}
          </NextIntlClientProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
