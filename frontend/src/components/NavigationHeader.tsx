// components/NavigationHeader.tsx - Client Component
'use client';

import { usePathname } from 'next/navigation';

export function NavigationHeader() {
  const pathname = usePathname();

  const isActive = (path: string) => {
    if (path === '/review') {
      return pathname === '/review' || pathname.startsWith('/review/');
    }
    return pathname === path || pathname.startsWith(path + '/');
  };

  const navLinkClass = (path: string) => 
    `text-sm transition-colors px-3 py-2 rounded-md flex items-center gap-2 ${
      isActive(path)
        ? 'text-blue-600 bg-blue-50 font-medium'
        : 'text-muted-foreground hover:text-foreground hover:bg-gray-100'
    }`;

  return (
    <nav className="border-b bg-white">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <h1 className="text-xl font-bold">Educational Content System</h1>
            <div className="flex space-x-2">
              <a href="/library" className={navLinkClass('/library')}>
                📚 Library
              </a>
              <a href="/generate" className={navLinkClass('/generate')}>
                ✨ Generate
              </a>
              <a href="/review" className={navLinkClass('/review')}>
                📋 Review
              </a>
              <a href="/test" className={navLinkClass('/test')}>
                🧪 Test
              </a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm text-muted-foreground">
              Teacher Review Interface
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}