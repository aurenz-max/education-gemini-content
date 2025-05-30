// src/app/review/page.tsx - Fixed Review Dashboard
'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ContentPackage } from '@/lib/types';
import { useContent } from '@/lib/context';
import { 
  Loader2, 
  Search, 
  Filter, 
  Eye, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  RefreshCw,
  ArrowLeft
} from 'lucide-react';

const STATUS_OPTIONS = [
  { value: 'all', label: 'All Status' },
  { value: 'generated', label: 'Pending Review' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'needs_revision', label: 'Needs Revision' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' }
];

export default function ReviewDashboard() {
  const router = useRouter();
  const { packages, loading, error, refreshPackages } = useContent();
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [subjectFilter, setSubjectFilter] = useState<string>('all');
  const [unitFilter, setUnitFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('generated'); // Default to pending review
  const [sortBy, setSortBy] = useState('newest');
  
  // Get unique subjects and units for filter options - safely calculated
  const subjects = useMemo(() => {
    if (!Array.isArray(packages)) return [];
    return Array.from(new Set(packages.map(pkg => pkg.subject))).sort();
  }, [packages]);
  
  const units = useMemo(() => {
    if (!Array.isArray(packages)) return [];
    return Array.from(new Set(
      packages
        .filter(pkg => subjectFilter === 'all' || pkg.subject === subjectFilter)
        .map(pkg => pkg.unit)
    )).sort();
  }, [packages, subjectFilter]);

  const loadPackages = async () => {
    await refreshPackages();
  };

  useEffect(() => {
    refreshPackages();
  }, [refreshPackages]);

  // Filter and sort packages - similar to library page
  const filteredPackages = useMemo(() => {
    // Ensure packages is always an array
    let filtered = Array.isArray(packages) ? [...packages] : [];

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(pkg => 
        (pkg.skill || '').toLowerCase().includes(term) ||
        (pkg.subskill || '').toLowerCase().includes(term) ||
        (pkg.subject || '').toLowerCase().includes(term) ||
        (pkg.unit || '').toLowerCase().includes(term)
      );
    }

    // Subject filter
    if (subjectFilter !== 'all') {
      filtered = filtered.filter(pkg => pkg.subject === subjectFilter);
    }

    // Unit filter
    if (unitFilter !== 'all') {
      filtered = filtered.filter(pkg => pkg.unit === unitFilter);
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(pkg => (pkg.status || 'generated') === statusFilter);
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
        case 'priority':
          // Prioritize packages that need review
          const statusPriority = { 'generated': 0, 'needs_revision': 1, 'under_review': 2, 'approved': 3, 'rejected': 4 };
          const aStatus = a.status || 'generated';
          const bStatus = b.status || 'generated';
          return (statusPriority[aStatus] || 0) - (statusPriority[bStatus] || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [packages, searchTerm, subjectFilter, unitFilter, statusFilter, sortBy]);

  // Statistics - similar to library page
  const stats = useMemo(() => {
    const safePackages = Array.isArray(packages) ? packages : [];
    const total = safePackages.length;
    
    const pendingReview = safePackages.filter(p => (p.status || 'generated') === 'generated').length;
    const approved = safePackages.filter(p => p.status === 'approved').length;
    const needsRevision = safePackages.filter(p => p.status === 'needs_revision').length;
    const rejected = safePackages.filter(p => p.status === 'rejected').length;
    const underReview = safePackages.filter(p => p.status === 'under_review').length;

    return { total, pendingReview, approved, needsRevision, rejected, underReview };
  }, [packages]);

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'needs_revision':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
      case 'under_review':
        return <Clock className="h-4 w-4 text-blue-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadge = (status?: string) => {
    const displayStatus = status || 'generated';
    switch (displayStatus) {
      case 'approved':
        return <Badge className="bg-green-100 text-green-800">Approved</Badge>;
      case 'rejected':
        return <Badge className="bg-red-100 text-red-800">Rejected</Badge>;
      case 'needs_revision':
        return <Badge className="bg-yellow-100 text-yellow-800">Needs Revision</Badge>;
      case 'under_review':
        return <Badge className="bg-blue-100 text-blue-800">Under Review</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Pending Review</Badge>;
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
      
      if (diffHours < 1) return 'Just now';
      if (diffHours < 24) return `${diffHours} hours ago`;
      
      const diffDays = Math.floor(diffHours / 24);
      if (diffDays < 7) return `${diffDays} days ago`;
      
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      });
    } catch {
      return 'Unknown';
    }
  };

  const handleReviewPackage = (pkg: ContentPackage) => {
    const params = new URLSearchParams({
      subject: pkg.subject,
      unit: pkg.unit
    });
    router.push(`/review/${pkg.id}?${params.toString()}`);
  };

  const clearFilters = () => {
    setSearchTerm('');
    setSubjectFilter('all');
    setUnitFilter('all');
    setStatusFilter('generated');
    setSortBy('newest');
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p>Loading packages for review...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 min-h-screen bg-gray-50">
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
        </div>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight">Review Dashboard</h1>
            <p className="text-xl text-muted-foreground mt-2">
              Review and approve generated content packages
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
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Pending Review</p>
                <p className="text-2xl font-bold">{stats.pendingReview}</p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Under Review</p>
                <p className="text-2xl font-bold">{stats.underReview}</p>
              </div>
              <Clock className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Approved</p>
                <p className="text-2xl font-bold">{stats.approved}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Need Changes</p>
                <p className="text-2xl font-bold">{stats.needsRevision}</p>
              </div>
              <AlertCircle className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Rejected</p>
                <p className="text-2xl font-bold">{stats.rejected}</p>
              </div>
              <XCircle className="h-8 w-8 text-red-600" />
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
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search skills, subjects..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={subjectFilter} onValueChange={setSubjectFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Subjects" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Subjects</SelectItem>
                {subjects.map(subject => (
                  <SelectItem key={subject} value={subject}>{subject}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={unitFilter} onValueChange={setUnitFilter}>
              <SelectTrigger>
                <SelectValue placeholder="All Units" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Units</SelectItem>
                {units.map(unit => (
                  <SelectItem key={unit} value={unit}>{unit}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by Status" />
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
                <SelectItem value="priority">By Priority</SelectItem>
                <SelectItem value="newest">Newest First</SelectItem>
                <SelectItem value="oldest">Oldest First</SelectItem>
                <SelectItem value="subject">By Subject</SelectItem>
              </SelectContent>
            </Select>
            
            <Button variant="outline" onClick={clearFilters}>
              Clear Filters
            </Button>
          </div>
          
          {/* Active Filters */}
          {(searchTerm || subjectFilter !== 'all' || unitFilter !== 'all' || statusFilter !== 'generated') && (
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-sm text-muted-foreground">Active filters:</span>
              {searchTerm && (
                <Badge variant="secondary">
                  Search: "{searchTerm}"
                </Badge>
              )}
              {subjectFilter !== 'all' && (
                <Badge variant="secondary">
                  Subject: {subjectFilter}
                </Badge>
              )}
              {unitFilter !== 'all' && (
                <Badge variant="secondary">
                  Unit: {unitFilter}
                </Badge>
              )}
              {statusFilter !== 'generated' && (
                <Badge variant="secondary">
                  Status: {STATUS_OPTIONS.find(s => s.value === statusFilter)?.label}
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
            <h3 className="font-medium text-red-800">Error Loading Review Queue</h3>
            <p className="text-sm text-red-600 mt-1">{error}</p>
            <Button variant="outline" size="sm" className="mt-2" onClick={loadPackages}>
              Try Again
            </Button>
          </div>
        </div>
      )}

      {/* Package Cards */}
      {filteredPackages.length === 0 ? (
        <div className="text-center py-12">
          <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <Clock className="h-12 w-12 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium mb-2">
            {packages.length === 0 ? 'No packages to review' : 'No packages match your filters'}
          </h3>
          <p className="text-muted-foreground mb-6">
            {packages.length === 0 
              ? 'All caught up! Check back later for new content to review.'
              : 'Try adjusting your search terms or filters.'
            }
          </p>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-muted-foreground">
              Showing {filteredPackages.length} of {packages.length} packages
            </p>
          </div>
          
          <div className="space-y-2">
            {filteredPackages.map((pkg) => (
              <Card key={pkg.id} className="hover:shadow-sm transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    {/* Left side - Content info */}
                    <div className="flex items-center space-x-4 flex-1">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(pkg.status)}
                        {getStatusBadge(pkg.status)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <h3 className="font-semibold text-lg truncate">{pkg.skill}</h3>
                          <span className="text-sm text-muted-foreground">•</span>
                          <p className="text-sm text-muted-foreground truncate">{pkg.subskill}</p>
                        </div>
                        <div className="flex items-center space-x-4 mt-1">
                          <span className="text-sm font-medium text-blue-700">{pkg.subject}</span>
                          <span className="text-sm text-muted-foreground">{pkg.unit}</span>
                          {pkg.generation_metadata && (
                            <span className="text-xs text-muted-foreground">
                              Quality: {Math.round((pkg.generation_metadata.coherence_score || 0) * 100)}%
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* Right side - Actions and date */}
                    <div className="flex items-center space-x-4">
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {formatDate(pkg.created_at)}
                      </span>
                      <Button 
                        onClick={() => handleReviewPackage(pkg)}
                        size="sm"
                        className="whitespace-nowrap"
                      >
                        <Eye className="mr-2 h-4 w-4" />
                        Review
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}