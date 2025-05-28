// lib/context.tsx
'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { ContentPackage, GenerationRequest, PackageFilters } from './types';
import { contentAPI } from './api';

interface ContentContextType {
  // State
  packages: ContentPackage[];
  loading: boolean;
  error: string | null;
  
  // Actions
  refreshPackages: (filters?: PackageFilters) => Promise<void>;
  generateContent: (request: GenerationRequest) => Promise<string>;
  deletePackage: (packageId: string, subject: string, unit: string) => Promise<void>;
  getPackage: (packageId: string, subject: string, unit: string) => Promise<ContentPackage>;
  clearError: () => void;
}

const ContentContext = createContext<ContentContextType | null>(null);

export function ContentProvider({ children }: { children: ReactNode }) {
  const [packages, setPackages] = useState<ContentPackage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const refreshPackages = useCallback(async (filters?: PackageFilters) => {
    setLoading(true);
    setError(null);
    try {
      const data = await contentAPI.listContentPackages(filters);
      setPackages(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load packages';
      setError(message);
      console.error('Failed to refresh packages:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const generateContent = useCallback(async (request: GenerationRequest): Promise<string> => {
    setLoading(true);
    setError(null);
    try {
      const result = await contentAPI.generateContent(request);
      
      // Add the new package to our state
      setPackages(prev => [result, ...prev]);
      
      return result.id;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate content';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deletePackage = useCallback(async (packageId: string, subject: string, unit: string) => {
    setLoading(true);
    setError(null);
    try {
      const success = await contentAPI.deleteContentPackage(packageId, subject, unit);
      
      if (success) {
        // Remove from local state
        setPackages(prev => prev.filter(pkg => pkg.id !== packageId));
      } else {
        throw new Error('Failed to delete package');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete package';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getPackage = useCallback(async (packageId: string, subject: string, unit: string): Promise<ContentPackage> => {
    setLoading(true);
    setError(null);
    try {
      const packageData = await contentAPI.getContentPackage(packageId, subject, unit);
      
      // Update the package in our local state if it exists
      setPackages(prev => prev.map(pkg => 
        pkg.id === packageId ? packageData : pkg
      ));
      
      return packageData;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get package';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const value: ContentContextType = {
    packages,
    loading,
    error,
    refreshPackages,
    generateContent,
    deletePackage,
    getPackage,
    clearError,
  };

  return (
    <ContentContext.Provider value={value}>
      {children}
    </ContentContext.Provider>
  );
}

export function useContent(): ContentContextType {
  const context = useContext(ContentContext);
  if (!context) {
    throw new Error('useContent must be used within a ContentProvider');
  }
  return context;
}