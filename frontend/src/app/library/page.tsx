// src/app/library/page.tsx
'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ContentPackageCard } from '@/components/ContentPackageCard';
import { useContent } from '@/lib/context';
import { ContentPackage, GenerationRequest } from '@/lib/types';
import { 
  Plus, 
  Search, 
  Filter, 
  ArrowLeft,
  Loader2,
  RefreshCw,
  FileText,
  BarChart3
} from 'lucide-react';

const SUBJECTS = [
  'Mathematics',
  'Science', 
  'English Language Arts',
  'Social Studies',
  'Computer Science',
  'Art',
  'Music',
  'Physical Education'
];

const STATUS_OPTIONS = [
  { value: 'all', label: 'All Status' },
  { value: 'draft', label: 'Draft' },
  { value: 'generated', label: 'Generated' },
  { value: 'approved', label: 'Approved' },
  { value: 'published', label: 'Published' }
];

export default function LibraryPage() {
  const router = useRouter();
  const { packages, loading, error, refreshPackages, deletePackage, generateContent } = useContent();
  
  // Filters and search
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [sortBy, setSortBy] = useState('newest');

  // Load packages on mount
  useEffect(() => {
    refreshPackages();
  }, [refreshPackages]);

  // Filter and sort packages
  const filteredPackages = useMemo(() => {
    let filtered = packages;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(pkg => 
        pkg.skill.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pkg.subskill.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pkg.unit.toLowerCase().includes(searchTerm.toLowerCase()) ||
        pkg.subject.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Subject filter
    if (selectedSubject !== 'all') {
      filtered = filtered.filter(pkg => pkg.subject === selectedSubject);
    }

    // Status filter
    if (selectedStatus !== 'all') {
      filtered = filtered.filter(pkg => (pkg.status || 'generated') === selectedStatus);
    }

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
        case 'oldest':
          return new Date(a.created_at || 0).getTime() - new Date(b.created_at || 0).getTime();
        case 'subject':
          return a.subject.localeCompare(b.subject);
        case 'coherence':
          return (b.generation_metadata?.coherence_score || 0) - (a.generation_metadata?.coherence_score || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [packages, searchTerm, selectedSubject, selectedStatus, sortBy]);

  // Statistics
  const stats = useMemo(() => {
    const total = packages.length;
    const byStatus = packages.reduce((acc, pkg) => {
      const status = pkg.status || 'generated';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const bySubject = packages.reduce((acc, pkg) => {
      acc[pkg.subject] = (acc[pkg.subject] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const avgCoherence = packages.length > 0 
      ? packages.reduce((sum, pkg) => sum + (pkg.generation_metadata?.coherence_score || 0), 0) / packages.length
      : 0;

    return { total, byStatus, bySubject, avgCoherence };
  }, [packages]);

  const handleDelete = async (packageId: string) => {
    const pkg = packages.find(p => p.id === packageId);
    if (pkg) {
      await deletePackage(packageId, pkg.subject, pkg.unit);
    }
  };

  const handleDuplicate = async (packageData: ContentPackage) => {
    const request: GenerationRequest = {
      subject: packageData.subject,
      unit: packageData.unit,
      skill: packageData.skill,
      subskill: `Copy of ${packageData.subskill}`,
      difficulty_level: packageData.master_context?.difficulty_level || 'intermediate',
      prerequisites: packageData.master_context?.prerequisites || []
    };

    try {
      await generateContent(request);
      router.push('/generate');
    } catch (error) {
      console.error('Failed to duplicate package:', error);
    }
  };

  const clearFilters = () => {
    setSearchTerm('');
    setSelectedSubject('all');
    setSelectedStatus('all');
    setSortBy('newest');
  };

  return (
    <div className="container mx-auto px-4 py-8 min-h-screen bg-gray-50">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <Button 
            variant="outline" 
            onClick={() => router.push('/')}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Home
          </Button>
          <Button 
            onClick={() => router.push('/generate')}
            className="flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Generate New Content
          </Button>
        </div>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight">Content Library</h1>
            <p className="text-xl text-muted-foreground mt-2">
              Manage and review your educational content packages
            </p>
          </div>
          
          <Button
            variant="outline"
            onClick={() => refreshPackages()}
            disabled={loading}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Packages</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Generated</p>
                <p className="text-2xl font-bold">{stats.byStatus.generated || 0}</p>
              </div>
              <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Approved</p>
                <p className="text-2xl font-bold">{stats.byStatus.approved || 0}</p>
              </div>
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Coherence</p>
                <p className="text-2xl font-bold">{Math.round(stats.avgCoherence * 100)}%</p>
              </div>
              <BarChart3 className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filter & Search
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search skills, subjects..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={selectedSubject} onValueChange={setSelectedSubject}>
              <SelectTrigger>
                <SelectValue placeholder="All Subjects" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Subjects</SelectItem>
                {SUBJECTS.map(subject => (
                  <SelectItem key={subject} value={subject}>
                    {subject}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger>
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                {STATUS_OPTIONS.map(option => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger>
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="newest">Newest First</SelectItem>
                <SelectItem value="oldest">Oldest First</SelectItem>
                <SelectItem value="subject">By Subject</SelectItem>
                <SelectItem value="coherence">By Coherence</SelectItem>
              </SelectContent>
            </Select>
            
            <Button variant="outline" onClick={clearFilters}>
              Clear Filters
            </Button>
          </div>
          
          {/* Active Filters */}
          {(searchTerm || selectedSubject !== 'all' || selectedStatus !== 'all') && (
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-sm text-muted-foreground">Active filters:</span>
              {searchTerm && (
                <Badge variant="secondary">
                  Search: "{searchTerm}"
                </Badge>
              )}
              {selectedSubject !== 'all' && (
                <Badge variant="secondary">
                  Subject: {selectedSubject}
                </Badge>
              )}
              {selectedStatus !== 'all' && (
                <Badge variant="secondary">
                  Status: {selectedStatus}
                </Badge>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <div className="mb-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="font-medium text-red-800">Error Loading Library</h3>
            <p className="text-sm text-red-600 mt-1">{error}</p>
            <Button variant="outline" size="sm" className="mt-2" onClick={() => refreshPackages()}>
              Try Again
            </Button>
          </div>
        </div>
      )}

      {/* Content Grid */}
      {loading && packages.length === 0 ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground">Loading content packages...</p>
          </div>
        </div>
      ) : filteredPackages.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <FileText className="h-12 w-12 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium mb-2">
            {packages.length === 0 ? 'No content packages yet' : 'No packages match your filters'}
          </h3>
          <p className="text-muted-foreground mb-6">
            {packages.length === 0 
              ? 'Generate your first educational content package to get started.'
              : 'Try adjusting your search terms or filters.'
            }
          </p>
          {packages.length === 0 && (
            <Button onClick={() => router.push('/generate')}>
              <Plus className="mr-2 h-4 w-4" />
              Generate First Package
            </Button>
          )}
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-muted-foreground">
              Showing {filteredPackages.length} of {packages.length} packages
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredPackages.map(pkg => (
              <ContentPackageCard
                key={pkg.id}
                package={pkg}
                onDelete={handleDelete}
                onDuplicate={handleDuplicate}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}