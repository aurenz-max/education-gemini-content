// components/review/RevisionHistory.tsx
'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  History, 
  Clock, 
  User, 
  FileText, 
  Eye, 
  Volume2, 
  BookOpen,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  XCircle
} from 'lucide-react';
import { RevisionHistory as RevisionHistoryType, ComponentType } from '@/lib/types';

interface RevisionHistoryProps {
  packageId: string;
  subject: string;
  unit: string;
  revisionHistory: RevisionHistoryType[];
  onRefresh: () => void;
}

export function RevisionHistory({ 
  packageId, 
  subject, 
  unit, 
  revisionHistory,
  onRefresh 
}: RevisionHistoryProps) {
  const [expandedRevisions, setExpandedRevisions] = useState<string[]>([]);

  const toggleRevision = (revisionId: string) => {
    setExpandedRevisions(prev => 
      prev.includes(revisionId) 
        ? prev.filter(id => id !== revisionId)
        : [...prev, revisionId]
    );
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return {
        date: date.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric'
        }),
        time: date.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit'
        })
      };
    } catch {
      return { date: 'Unknown', time: '' };
    }
  };

  const getComponentIcon = (componentType: ComponentType) => {
    const icons = {
      reading: FileText,
      visual: Eye,
      audio: Volume2,
      practice: BookOpen
    };
    return icons[componentType] || FileText;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'in_progress':
        return <AlertCircle className="h-4 w-4 text-yellow-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (revisionHistory.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Revision History
            </CardTitle>
            <Button variant="outline" size="sm" onClick={onRefresh}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Alert>
            <History className="h-4 w-4" />
            <AlertDescription>
              No revisions have been made to this content package yet. Use the "Request Changes" buttons in the content panels to create revision requests.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Revision History
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {revisionHistory.length} revision{revisionHistory.length !== 1 ? 's' : ''}
            </Badge>
            <Button variant="outline" size="sm" onClick={onRefresh}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {revisionHistory.map((revision, index) => {
            const { date, time } = formatTimestamp(revision.timestamp);
            const isExpanded = expandedRevisions.includes(revision.revision_id);
            
            return (
              <div 
                key={revision.revision_id} 
                className="border rounded-lg p-4 space-y-3"
              >
                {/* Revision Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(revision.status)}
                      <div>
                        <p className="font-medium text-sm">
                          Revision #{revisionHistory.length - index}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {date} at {time}
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <Badge className={getStatusColor(revision.status)}>
                      {revision.status.replace('_', ' ')}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleRevision(revision.revision_id)}
                    >
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                {/* Components Revised */}
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm text-muted-foreground">Components:</span>
                  {revision.components_revised.map(componentType => {
                    const Icon = getComponentIcon(componentType);
                    return (
                      <Badge key={componentType} variant="secondary" className="text-xs">
                        <Icon className="mr-1 h-3 w-3" />
                        {componentType.charAt(0).toUpperCase() + componentType.slice(1)}
                      </Badge>
                    );
                  })}
                </div>

                {/* Feedback Summary */}
                <div className="bg-gray-50 rounded p-3">
                  <p className="text-sm">
                    <span className="font-medium">Feedback: </span>
                    {revision.feedback_summary}
                  </p>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="border-t pt-3 space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Revision ID:</span>
                        <p className="font-mono text-xs break-all">{revision.revision_id}</p>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Revised By:</span>
                        <p className="flex items-center gap-1 mt-1">
                          <User className="h-3 w-3" />
                          {revision.revised_by}
                        </p>
                      </div>
                    </div>

                    {/* Status Details */}
                    {revision.status === 'in_progress' && (
                      <Alert>
                        <AlertCircle className="h-4 w-4" />
                        <AlertDescription>
                          This revision is currently being processed. Check back in a few minutes for updates.
                        </AlertDescription>
                      </Alert>
                    )}

                    {revision.status === 'failed' && (
                      <Alert variant="destructive">
                        <XCircle className="h-4 w-4" />
                        <AlertDescription>
                          This revision failed to process. You may need to submit a new revision request.
                        </AlertDescription>
                      </Alert>
                    )}

                    {revision.status === 'completed' && (
                      <Alert>
                        <CheckCircle2 className="h-4 w-4" />
                        <AlertDescription>
                          Revision completed successfully. The updated content is now available for review.
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Summary Stats */}
        <div className="mt-6 pt-4 border-t">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-green-600">
                {revisionHistory.filter(r => r.status === 'completed').length}
              </p>
              <p className="text-sm text-muted-foreground">Completed</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-yellow-600">
                {revisionHistory.filter(r => r.status === 'in_progress').length}
              </p>
              <p className="text-sm text-muted-foreground">In Progress</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">
                {revisionHistory.filter(r => r.status === 'failed').length}
              </p>
              <p className="text-sm text-muted-foreground">Failed</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}