// components/NavigationHeader.tsx - Client Component
'use client';

import { Badge } from '@/components/ui/badge';
import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { contentAPI } from '@/lib/api';

export function NavigationHeader() {
  const pathname = usePathname();
  const [reviewCount, setReviewCount] = useState<number>(0);
  const [isLoading, setIsLoading] = useState(true);

  // Load review queue count
  useEffect(() => {
    const loadReviewCount = async () => {
      try {
        const packages = await contentAPI.getReviewQueue({ limit: 100 });
        setReviewCount(packages.length);
      } catch (error) {
        console.error('Failed to load review count:', error);
        setReviewCount(0);
      } finally {
        setIsLoading(false);
      }
    };

    loadReviewCount();
    
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      loadReviewCount();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

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
                <span>📋 Review</span>
                {!isLoading && reviewCount > 0 && (
                  <Badge className="bg-red-500 text-white text-xs ml-1 px-1.5 py-0.5 min-w-5 h-5 flex items-center justify-center">
                    {reviewCount > 99 ? '99+' : reviewCount}
                  </Badge>
                )}
                {isLoading && (
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse ml-1"></div>
                )}
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
            {!isLoading && reviewCount > 0 && (
              <div className="text-xs text-orange-600 font-medium">
                {reviewCount} package{reviewCount !== 1 ? 's' : ''} awaiting review
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}