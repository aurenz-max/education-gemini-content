// src/components/review/ReviewActions.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { contentAPI } from '@/lib/api';
import { 
  Check, 
  X, 
  AlertTriangle, 
  MessageSquare, 
  Loader2,
  Clock,
  User
} from 'lucide-react';

interface ReviewActionsProps {
  packageId: string;
  subject: string;
  unit: string;
  currentStatus?: string;
  onStatusUpdate: (newStatus: string) => void;
  reviewHistory?: Array<{
    note: string;
    status: string;
    timestamp: string;
    reviewer_id: string;
  }>;
}

export function ReviewActions({ 
  packageId, 
  subject, 
  unit, 
  currentStatus = 'generated',
  onStatusUpdate,
  reviewHistory = []
}: ReviewActionsProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const [activeDialog, setActiveDialog] = useState<string | null>(null);

  // Mock reviewer ID - in a real app, this would come from authentication
  const reviewerId = 'educator_123';

  const handleStatusUpdate = async (
    status: 'approved' | 'rejected' | 'needs_revision',
    notes: string
  ) => {
    if (!notes.trim() && status !== 'approved') {
      alert('Please provide review notes');
      return;
    }

    setIsSubmitting(true);

    try {
      const result = await contentAPI.updatePackageStatus(packageId, subject, unit, {
        status,
        reviewer_id: reviewerId,
        notes: notes.trim() || getDefaultMessage(status)
      });

      console.log('✅ Status updated successfully:', result);
      
      // Update parent component
      onStatusUpdate(status);
      
      // Close dialog and reset form
      setActiveDialog(null);
      setReviewNotes('');
      
      // Show success message
      const successMessage = `Package ${
        status === 'approved' ? 'approved' : 
        status === 'rejected' ? 'rejected' : 
        'marked for revision'
      } successfully!`;
      
      alert(successMessage);
      
    } catch (error) {
      console.error('❌ Failed to update status:', error);
      const errorMessage = `Failed to ${status} package: ${
        error instanceof Error ? error.message : 'Unknown error'
      }`;
      alert(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getDefaultMessage = (status: string) => {
    switch (status) {
      case 'approved':
        return 'Package approved for publication';
      case 'rejected':
        return 'Package rejected - needs significant improvements';
      case 'needs_revision':
        return 'Package needs minor revisions before approval';
      default:
        return 'Status updated';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
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
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'needs_revision':
        return 'bg-yellow-100 text-yellow-800';
      case 'under_review':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const ActionButton = ({ 
    status, 
    icon: Icon, 
    children, 
    variant = "default" 
  }: { 
    status: 'approved' | 'rejected' | 'needs_revision';
    icon: any;
    children: React.ReactNode;
    variant?: "default" | "destructive" | "outline";
  }) => {
    const handleDialogOpenChange = (open: boolean) => {
      setActiveDialog(open ? status : null);
      if (!open) {
        // Reset notes when closing dialog
        setReviewNotes('');
      }
    };

    const handleNotesChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setReviewNotes(e.target.value);
    };

    const handleConfirm = () => {
      handleStatusUpdate(status, reviewNotes);
    };

    return (
      <Dialog open={activeDialog === status} onOpenChange={handleDialogOpenChange}>
        <DialogTrigger asChild>
          <Button variant={variant} className="flex-1">
            <Icon className="mr-2 h-4 w-4" />
            {children}
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {status === 'approved' && 'Approve Package'}
              {status === 'rejected' && 'Reject Package'}
              {status === 'needs_revision' && 'Request Changes'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="notes">Review Notes</Label>
              <Textarea
                id="notes"
                placeholder={
                  status === 'approved' 
                    ? 'Optional: Add any final comments...'
                    : 'Please explain what needs to be addressed...'
                }
                value={reviewNotes}
                onChange={handleNotesChange}
                rows={4}
                className="mt-1"
              />
            </div>
            
            <div className="flex gap-2 justify-end">
              <Button 
                variant="outline" 
                onClick={() => handleDialogOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirm}
                disabled={isSubmitting}
                variant={status === 'rejected' ? 'destructive' : 'default'}
              >
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Confirm {status === 'approved' ? 'Approval' : status === 'rejected' ? 'Rejection' : 'Changes'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  return (
    <div className="space-y-6">
      {/* Current Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Review Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3 mb-4">
            <Badge className={getStatusColor(currentStatus)}>
              {currentStatus === 'generated' ? 'Pending Review' : 
               currentStatus.charAt(0).toUpperCase() + currentStatus.slice(1).replace('_', ' ')}
            </Badge>
            <span className="text-sm text-muted-foreground">
              Package ID: {packageId}
            </span>
          </div>
          
          {currentStatus === 'generated' && (
            <p className="text-sm text-muted-foreground">
              This package is awaiting initial review. Please examine all content components before making a decision.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Review Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Review Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <ActionButton status="approved" icon={Check} variant="default">
              Approve
            </ActionButton>
            <ActionButton status="needs_revision" icon={AlertTriangle} variant="outline">
              Request Changes
            </ActionButton>
            <ActionButton status="rejected" icon={X} variant="destructive">
              Reject
            </ActionButton>
          </div>
          
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Review Guidelines:</strong> Approved packages will be published to the library. 
              Rejected packages will be archived. Packages needing revision will return to the generation queue.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Review History */}
      {reviewHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Review History
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {reviewHistory.map((review, index) => (
                <div key={index} className="border-l-2 border-gray-200 pl-4 pb-4 last:pb-0">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className={getStatusColor(review.status)} size="sm">
                      {review.status.replace('_', ' ')}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {formatTimestamp(review.timestamp)}
                    </span>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <User className="h-3 w-3" />
                      {review.reviewer_id}
                    </div>
                  </div>
                  {review.note && (
                    <p className="text-sm text-gray-700 bg-gray-50 p-2 rounded">
                      {review.note}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Stats */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-2 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-green-600">
                {reviewHistory.filter(r => r.status === 'approved').length}
              </p>
              <p className="text-sm text-muted-foreground">Approvals</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600">
                {reviewHistory.length}
              </p>
              <p className="text-sm text-muted-foreground">Total Reviews</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}