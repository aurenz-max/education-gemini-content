// src/app/review/page.tsx - Review Dashboard
'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ContentPackage } from '@/lib/types';
import { contentAPI } from '@/lib/api';
import { 
  Loader2, 
  Search, 
  Filter, 
  Eye, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  RefreshCw 
} from 'lucide-react';

export default function ReviewDashboard() {
  const router = useRouter();
  const [packages, setPackages] = useState<ContentPackage[]>([]);
  const [filteredPackages, setFilteredPackages] = useState<ContentPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [subjectFilter, setSubjectFilter] = useState<string>('all');
  const [unitFilter, setUnitFilter] = useState<string>('all');
  
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
    try {
      setLoading(true);
      setError(null);
      
      const reviewQueue = await contentAPI.getReviewQueue({ limit: 100 });
      setPackages(reviewQueue);
      setFilteredPackages(reviewQueue);
      
    } catch (err) {
      console.error('Failed to load review queue:', err);
      setError(err instanceof Error ? err.message : 'Failed to load packages');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPackages();
  }, []);

  // Apply filters
  useEffect(() => {
    if (!Array.isArray(packages)) {
      setFilteredPackages([]);
      return;
    }

    let filtered = [...packages]; // Create a copy

    // Apply subject filter
    if (subjectFilter !== 'all') {
      filtered = filtered.filter(pkg => pkg.subject === subjectFilter);
    }

    // Apply unit filter
    if (unitFilter !== 'all') {
      filtered = filtered.filter(pkg => pkg.unit === unitFilter);
    }

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(pkg => 
        (pkg.skill || '').toLowerCase().includes(term) ||
        (pkg.subskill || '').toLowerCase().includes(term) ||
        (pkg.subject || '').toLowerCase().includes(term) ||
        (pkg.unit || '').toLowerCase().includes(term)
      );
    }

    setFilteredPackages(filtered);
  }, [packages, searchTerm, subjectFilter, unitFilter]);

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
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold">Review Dashboard</h1>
            <p className="text-muted-foreground text-lg">
              Review and approve generated content packages
            </p>
          </div>
          <Button onClick={loadPackages} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="text-2xl font-bold">{filteredPackages.length}</p>
                  <p className="text-sm text-muted-foreground">Awaiting Review</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-2xl font-bold">
                    {Array.isArray(packages) ? packages.filter(p => p.status === 'approved').length : 0}
                  </p>
                  <p className="text-sm text-muted-foreground">Approved</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-yellow-600" />
                <div>
                  <p className="text-2xl font-bold">
                    {Array.isArray(packages) ? packages.filter(p => p.status === 'needs_revision').length : 0}
                  </p>
                  <p className="text-sm text-muted-foreground">Need Changes</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <XCircle className="h-5 w-5 text-red-600" />
                <div>
                  <p className="text-2xl font-bold">
                    {Array.isArray(packages) ? packages.filter(p => p.status === 'rejected').length : 0}
                  </p>
                  <p className="text-sm text-muted-foreground">Rejected</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by skill, subject, or unit..."
                  className="pl-10"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
            
            <Select value={subjectFilter} onValueChange={setSubjectFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by Subject" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Subjects</SelectItem>
                {subjects.map(subject => (
                  <SelectItem key={subject} value={subject}>{subject}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={unitFilter} onValueChange={setUnitFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by Unit" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Units</SelectItem>
                {units.map(unit => (
                  <SelectItem key={unit} value={unit}>{unit}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-800">
              <AlertCircle className="h-5 w-5" />
              <p>{error}</p>
              <Button onClick={loadPackages} size="sm" variant="outline" className="ml-auto">
                Retry
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Package Cards */}
      {filteredPackages.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <div className="text-muted-foreground">
              <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">No packages to review</h3>
              <p>All caught up! Check back later for new content to review.</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPackages.map((pkg) => (
            <Card key={pkg.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-lg leading-tight mb-1">
                      {pkg.skill}
                    </CardTitle>
                    <p className="text-sm text-muted-foreground truncate">
                      {pkg.subskill}
                    </p>
                  </div>
                  {getStatusIcon(pkg.status)}
                </div>
              </CardHeader>
              
              <CardContent className="pt-0">
                <div className="space-y-3">
                  <div className="text-sm">
                    <p className="font-medium text-blue-700">{pkg.subject}</p>
                    <p className="text-muted-foreground">{pkg.unit}</p>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    {getStatusBadge(pkg.status)}
                    <span className="text-xs text-muted-foreground">
                      {formatDate(pkg.created_at)}
                    </span>
                  </div>
                  
                  {pkg.generation_metadata && (
                    <div className="text-xs text-muted-foreground">
                      Quality: {Math.round((pkg.generation_metadata.coherence_score || 0) * 100)}%
                    </div>
                  )}
                  
                  <div className="flex gap-2 pt-2">
                    <Button 
                      onClick={() => handleReviewPackage(pkg)}
                      className="flex-1"
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
      )}
    </div>
  );
}