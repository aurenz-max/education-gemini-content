// src/app/review/[packageId]/page.tsx - Updated for Enhanced Visual Demo Panel
'use client';

import { useState, useEffect, use } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useContent } from '@/lib/context';
import { ContentPackage, ComponentType } from '@/lib/types';
import { contentAPI, ReviewInfo, RevisionHistory } from '@/lib/api';
import { 
  ArrowLeft, 
  Loader2, 
  AlertCircle, 
  RefreshCw, 
  CheckCircle,
  History,
  Clock,
  User,
  Eye,
  FileText,
  Play,
  Headphones,
  BookOpen
} from 'lucide-react';

// Import updated panels with revision support
import { ReadingContentPanel } from '@/components/review/ReadingContentPanel';
import { VisualDemoPanel } from '@/components/review/VisualDemoPanel'; // This will use your enhanced component
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
  
  // Revision state - Initialize as empty array with proper typing
  const [isSubmittingRevision, setIsSubmittingRevision] = useState(false);
  const [revisionComponent, setRevisionComponent] = useState<ComponentType | null>(null);
  const [revisionHistory, setRevisionHistory] = useState<RevisionHistory[]>([]);

  const subject = searchParams.get('subject') || '';
  const unit = searchParams.get('unit') || '';
  const reviewerId = 'educator_123'; // In real app, get from auth context

  // Load package content
  useEffect(() => {
    const loadPackage = async () => {
      if (!subject || !unit) {
        setLoadingPackage(false);
        return;
      }

      try {
        const pkg = await getPackage(packageId, subject, unit);
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

  // Load review information and revision history
  useEffect(() => {
    const loadReviewData = async () => {
      if (!subject || !unit) return;

      try {
        setLoadingReview(true);
        
        // Load review info and revision history in parallel
        const [reviewData, historyData] = await Promise.all([
          contentAPI.getPackageReviewInfo(packageId, subject, unit).catch(() => null),
          contentAPI.getRevisionHistory(packageId, subject, unit).catch(() => [])
        ]);

        if (reviewData) {
          setReviewInfo(reviewData);
          setCurrentStatus(reviewData.current_status);
        }
        
        // Ensure historyData is always an array
        setRevisionHistory(Array.isArray(historyData) ? historyData : []);
        
      } catch (err) {
        console.error('⚠️ Failed to load review data:', err);
        // Set empty array on error
        setRevisionHistory([]);
      } finally {
        setLoadingReview(false);
      }
    };

    if (packageId && subject && unit) {
      loadReviewData();
    }
  }, [packageId, subject, unit]);

  const handleRevisionRequest = async (
    componentType: ComponentType,
    feedback: string,
    priority: 'low' | 'medium' | 'high'
  ) => {
    if (!package_) return;

    try {
      setIsSubmittingRevision(true);
      setRevisionComponent(componentType);

      // Submit revision request
      const revisedPackage = await contentAPI.reviseContentPackage(
        packageId,
        subject,
        unit,
        [{
          component_type: componentType,
          feedback,
          priority
        }],
        reviewerId
      );

      // Update the package in state
      setPackage(revisedPackage);
      setCurrentStatus('needs_revision');

      // Refresh revision history
      try {
        const updatedHistory = await contentAPI.getRevisionHistory(packageId, subject, unit);
        setRevisionHistory(Array.isArray(updatedHistory) ? updatedHistory : []);
      } catch (historyError) {
        console.error('Failed to refresh revision history:', historyError);
      }

      alert(`${componentType.charAt(0).toUpperCase() + componentType.slice(1)} revision request submitted successfully!`);

    } catch (err) {
      console.error('❌ Revision request failed:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit revision request';
      alert(`Revision request failed: ${errorMessage}`);
    } finally {
      setIsSubmittingRevision(false);
      setRevisionComponent(null);
    }
  };

  // NEW: Package save handler
  const handleSavePackage = async () => {
    if (!package_) return;

    try {
      // Update package status to indicate it's been saved for review
      await contentAPI.updatePackageStatus(
        packageId,
        subject,
        unit,
        {
          status: 'under_review',
          reviewer_id: reviewerId,
          notes: 'Package saved and marked for review'
        }
      );
      
      setCurrentStatus('under_review');
      alert('Package saved successfully!');
      
    } catch (err) {
      console.error('❌ Failed to save package:', err);
      throw new Error(err instanceof Error ? err.message : 'Failed to save package');
    }
  };

  // NEW: Package approval handler
  const handleApprovePackage = async () => {
    if (!package_) return;

    try {
      await contentAPI.approvePackage(packageId, subject, unit, reviewerId, 'Package approved for publication');
      setCurrentStatus('approved');
      alert('Package approved successfully!');
      
    } catch (err) {
      console.error('❌ Failed to approve package:', err);
      throw new Error(err instanceof Error ? err.message : 'Failed to approve package');
    }
  };

  const handleStatusUpdate = (newStatus: string) => {
    setCurrentStatus(newStatus);
    if (subject && unit) {
      contentAPI.getPackageReviewInfo(packageId, subject, unit)
        .then(setReviewInfo)
        .catch(console.error);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Unknown';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'needs_revision':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'under_review':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // Safe array access with fallback
  const safeRevisionHistory = Array.isArray(revisionHistory) ? revisionHistory : [];

  // Component availability check
  const getAvailableComponents = () => {
    const components = [];
    if (package_?.content?.reading) components.push({ key: 'reading', label: 'Reading', icon: FileText });
    if (package_?.content?.visual) components.push({ key: 'visual', label: 'Visual Demo', icon: Eye });
    if (package_?.content?.audio) components.push({ key: 'audio', label: 'Audio', icon: Headphones });
    if (package_?.content?.practice) components.push({ key: 'practice', label: 'Practice', icon: BookOpen });
    return components;
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
        
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Could not load the requested content package.'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const availableComponents = getAvailableComponents();

  return (
    <div className="container mx-auto p-6 min-h-screen bg-gray-50">
      {/* Clean Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <Button variant="ghost" onClick={() => router.push('/review')} className="text-muted-foreground">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Review
          </Button>
          <div className="flex items-center gap-3">
            <Badge className={`${getStatusColor(currentStatus)} border`}>
              {currentStatus === 'generated' ? 'Pending Review' : 
               currentStatus.charAt(0).toUpperCase() + currentStatus.slice(1).replace('_', ' ')}
            </Badge>
            <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>
        
        <div className="space-y-1">
          <h1 className="text-3xl font-bold">{package_.skill}</h1>
          <p className="text-xl text-muted-foreground">{package_.subskill}</p>
          <p className="text-sm text-muted-foreground">
            {package_.subject} • {package_.unit} • Generated {formatDate(package_.created_at)}
            {package_.generation_metadata && (
              <span className="ml-2">• Quality: {Math.round((package_.generation_metadata.coherence_score || 0) * 100)}%</span>
            )}
          </p>
        </div>
      </div>

      {/* Revision Status Alert */}
      {isSubmittingRevision && (
        <Alert className="mb-6">
          <Loader2 className="h-4 w-4 animate-spin" />
          <AlertDescription>
            Processing {revisionComponent} revision request...
          </AlertDescription>
        </Alert>
      )}

      {/* Main Tabs */}
      <Tabs defaultValue="content" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="content">Content Review</TabsTrigger>
          <TabsTrigger value="actions">Review Actions</TabsTrigger>
          <TabsTrigger value="history">
            History ({safeRevisionHistory.length})
          </TabsTrigger>
        </TabsList>

        {/* Content Review Tab */}
        <TabsContent value="content" className="space-y-6">
          {/* Component Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Available Components ({availableComponents.length}/4)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {availableComponents.map(({ key, label, icon: Icon }) => (
                  <div key={key} className="flex items-center gap-2 p-3 bg-green-50 rounded-lg border border-green-200">
                    <Icon className="h-4 w-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800">{label}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Content Panels */}
          <div className="space-y-6">
            {package_.content?.reading && (
              <ReadingContentPanel 
                content={package_.content.reading}
                packageId={packageId}
                subject={subject}
                unit={unit}
                onRevisionRequest={(feedback, priority) => 
                  handleRevisionRequest('reading', feedback, priority)
                }
                isSubmittingRevision={isSubmittingRevision && revisionComponent === 'reading'}
              />
            )}

            {package_.content?.visual && (
              <VisualDemoPanel 
                content={package_.content.visual}
                packageId={packageId}
                subject={subject}
                unit={unit}
                onRevisionRequest={(feedback, priority) => 
                  handleRevisionRequest('visual', feedback, priority)
                }
                isSubmittingRevision={isSubmittingRevision && revisionComponent === 'visual'}
                onSavePackage={handleSavePackage}
                onApprovePackage={handleApprovePackage}
                packageStatus={currentStatus as any}
              />
            )}

            {package_.content?.audio && (
              <AudioContentPanel 
                content={package_.content.audio}
                packageId={packageId}
                subject={subject}
                unit={unit}
                onRevisionRequest={(feedback, priority) => 
                  handleRevisionRequest('audio', feedback, priority)
                }
                isSubmittingRevision={isSubmittingRevision && revisionComponent === 'audio'}
              />
            )}

            {package_.content?.practice && (
              <PracticeProblemsPanel 
                content={package_.content.practice}
                packageId={packageId}
                subject={subject}
                unit={unit}
                onRevisionRequest={(feedback, priority) => 
                  handleRevisionRequest('practice', feedback, priority)
                }
                isSubmittingRevision={isSubmittingRevision && revisionComponent === 'practice'}
              />
            )}
          </div>
        </TabsContent>

        {/* Review Actions Tab */}
        <TabsContent value="actions">
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
        </TabsContent>

        {/* Revision History Tab */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Revision History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {safeRevisionHistory.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No revisions have been made yet.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {safeRevisionHistory.map((revision, index) => (
                    <div key={revision.revision_id || index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">#{safeRevisionHistory.length - index}</Badge>
                          <span className="text-sm text-muted-foreground">
                            {formatDate(revision.timestamp)}
                          </span>
                        </div>
                        <Badge className={
                          revision.status === 'completed' ? 'bg-green-100 text-green-800' :
                          revision.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }>
                          {revision.status.replace('_', ' ')}
                        </Badge>
                      </div>
                      
                      {Array.isArray(revision.components_revised) && revision.components_revised.length > 0 && (
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm text-muted-foreground">Components:</span>
                          {revision.components_revised.map((comp: string) => (
                            <Badge key={comp} variant="secondary" className="text-xs">
                              {comp.charAt(0).toUpperCase() + comp.slice(1)}
                            </Badge>
                          ))}
                        </div>
                      )}
                      
                      {revision.feedback_summary && (
                        <div className="bg-gray-50 rounded p-3">
                          <p className="text-sm">{revision.feedback_summary}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}