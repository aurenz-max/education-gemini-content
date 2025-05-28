// src/app/review/[packageId]/page.tsx - Updated with Review Actions
'use client';

import { useState, useEffect, use } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useContent } from '@/lib/context';
import { ContentPackage } from '@/lib/types';
import { contentAPI, ReviewInfo } from '@/lib/api';
import { ArrowLeft, Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { ReadingContentPanel } from '@/components/review/ReadingContentPanel';
import { VisualDemoPanel } from '@/components/review/VisualDemoPanel';
import { AudioContentPanel } from '@/components/review/AudioContentPanel';
import { PracticeProblemsPanel } from '@/components/review/PracticeProblemsPanel';
import { ReviewActions } from '@/components/review/ReviewActions';

interface ReviewPageProps {
  params: Promise<{
    packageId: string;
  }>;
}

export default function ReviewPage({ params }: ReviewPageProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { getPackage, loading, error } = useContent();
  
  // Unwrap the params promise
  const { packageId } = use(params);
  
  const [package_, setPackage] = useState<ContentPackage | null>(null);
  const [reviewInfo, setReviewInfo] = useState<ReviewInfo | null>(null);
  const [loadingPackage, setLoadingPackage] = useState(true);
  const [loadingReview, setLoadingReview] = useState(true);
  const [currentStatus, setCurrentStatus] = useState<string>('generated');

  const subject = searchParams.get('subject') || '';
  const unit = searchParams.get('unit') || '';

  // Load package content
  useEffect(() => {
    const loadPackage = async () => {
      console.log('🔍 Loading package:', { packageId, subject, unit });

      if (!subject || !unit) {
        console.error('❌ Missing required parameters:', { subject, unit });
        setLoadingPackage(false);
        return;
      }

      try {
        const pkg = await getPackage(packageId, subject, unit);
        console.log('✅ Package loaded:', pkg);
        setPackage(pkg);
        setCurrentStatus(pkg.status || 'generated');
      } catch (err) {
        console.error('❌ Failed to load package:', err);
      } finally {
        setLoadingPackage(false);
      }
    };

    loadPackage();
  }, [packageId, subject, unit, getPackage]);

  // Load review information
  useEffect(() => {
    const loadReviewInfo = async () => {
      if (!subject || !unit) return;

      try {
        setLoadingReview(true);
        const info = await contentAPI.getPackageReviewInfo(packageId, subject, unit);
        console.log('📋 Review info loaded:', info);
        setReviewInfo(info);
        setCurrentStatus(info.current_status);
      } catch (err) {
        console.error('⚠️ Failed to load review info:', err);
        // Don't treat this as a critical error
      } finally {
        setLoadingReview(false);
      }
    };

    if (packageId && subject && unit) {
      loadReviewInfo();
    }
  }, [packageId, subject, unit]);

  const handleStatusUpdate = (newStatus: string) => {
    setCurrentStatus(newStatus);
    // Optionally reload the review info to get updated history
    if (subject && unit) {
      contentAPI.getPackageReviewInfo(packageId, subject, unit)
        .then(setReviewInfo)
        .catch(console.error);
    }
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Unknown';
    }
  };

  if (loadingPackage || loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p>Loading content package...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !package_) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Button variant="outline" onClick={() => router.push('/review')} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Review Dashboard
        </Button>
        
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <h3 className="font-medium text-red-800">Package Not Found</h3>
          </div>
          <p className="text-red-600 mb-4">
            {error || 'Could not load the requested content package.'}
          </p>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={() => router.push('/review')}>
              Review Dashboard
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 min-h-screen bg-gray-50">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Button variant="outline" onClick={() => router.push('/review')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Review Dashboard
            </Button>
            <Badge variant="secondary">Package ID: {package_.id}</Badge>
            <Badge className={
              currentStatus === 'approved' ? 'bg-green-100 text-green-800' :
              currentStatus === 'rejected' ? 'bg-red-100 text-red-800' :
              currentStatus === 'needs_revision' ? 'bg-yellow-100 text-yellow-800' :
              'bg-gray-100 text-gray-800'
            }>
              {currentStatus === 'generated' ? 'Pending Review' : 
               currentStatus.charAt(0).toUpperCase() + currentStatus.slice(1).replace('_', ' ')}
            </Badge>
          </div>
          <h1 className="text-3xl font-bold">Review Content Package</h1>
          <p className="text-muted-foreground text-lg">
            {package_.subject} → {package_.unit} → {package_.skill} → {package_.subskill}
          </p>
        </div>
        <Button variant="outline" onClick={handleRefresh}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Main Content Area - 3 columns */}
        <div className="xl:col-span-3">
          {/* Four-Panel Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6" style={{ minHeight: '600px' }}>
            {package_.content?.reading ? (
              <ReadingContentPanel content={package_.content.reading} />
            ) : (
              <Card className="h-full flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  <p>Reading content not available</p>
                </div>
              </Card>
            )}

            {package_.content?.visual ? (
              <VisualDemoPanel content={package_.content.visual} />
            ) : (
              <Card className="h-full flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  <p>Visual content not available</p>
                </div>
              </Card>
            )}

            {package_.content?.audio ? (
              <AudioContentPanel content={package_.content.audio} />
            ) : (
              <Card className="h-full flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  <p>Audio content not available</p>
                </div>
              </Card>
            )}

            {package_.content?.practice ? (
              <PracticeProblemsPanel content={package_.content.practice} />
            ) : (
              <Card className="h-full flex items-center justify-center">
                <div className="text-center text-muted-foreground">
                  <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                  <p>Practice content not available</p>
                </div>
              </Card>
            )}
          </div>

          {/* Package Metadata */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Package Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="font-medium text-muted-foreground">Generated</p>
                  <p>{formatDate(package_.created_at)}</p>
                </div>
                <div>
                  <p className="font-medium text-muted-foreground">Last Updated</p>
                  <p>{formatDate(package_.updated_at || package_.created_at)}</p>
                </div>
                {package_.generation_metadata && (
                  <>
                    <div>
                      <p className="font-medium text-muted-foreground">Generation Time</p>
                      <p>{Math.round(package_.generation_metadata.generation_time_ms / 1000)}s</p>
                    </div>
                    <div>
                      <p className="font-medium text-muted-foreground">Quality Score</p>
                      <p>{Math.round((package_.generation_metadata.coherence_score || 0) * 100)}%</p>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Review Actions Sidebar - 1 column */}
        <div className="xl:col-span-1">
          <div className="sticky top-6">
            {loadingReview ? (
              <Card>
                <CardContent className="p-6 text-center">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">Loading review info...</p>
                </CardContent>
              </Card>
            ) : (
              <ReviewActions
                packageId={packageId}
                subject={subject}
                unit={unit}
                currentStatus={currentStatus}
                onStatusUpdate={handleStatusUpdate}
                reviewHistory={reviewInfo?.review_notes || []}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}