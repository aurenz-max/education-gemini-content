// app/layout.tsx - Server Component Only
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ContentProvider } from '@/lib/context';
import { Toaster } from '@/components/ui/toaster';
import { NavigationHeader } from '@/components/NavigationHeader';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Educational Content Review System',
  description: 'AI-powered educational content generation and review system',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ContentProvider>
          <div className="min-h-screen bg-background">
            <NavigationHeader />
            <main>{children}</main>
          </div>
          <Toaster />
        </ContentProvider>
      </body>
    </html>
  );
}