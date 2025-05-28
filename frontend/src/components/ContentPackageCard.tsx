// src/components/ContentPackageCard.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { 
  Eye, 
  FileText, 
  Volume2, 
  BookOpen, 
  MoreHorizontal, 
  Pencil, 
  Copy, 
  Trash, 
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { ContentPackage } from '@/lib/types';
// No external date library needed - using built-in JavaScript

interface ContentPackageCardProps {
  package: ContentPackage;
  onDelete?: (packageId: string) => void;
  onDuplicate?: (packageData: ContentPackage) => void;
}

export function ContentPackageCard({ package: pkg, onDelete, onDuplicate }: ContentPackageCardProps) {
  const router = useRouter();
  const [isDeleting, setIsDeleting] = useState(false);

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'approved': return 'default';
      case 'published': return 'default';
      case 'generated': return 'secondary';
      case 'draft': return 'outline';
      default: return 'secondary';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
      case 'published':
        return <CheckCircle className="h-3 w-3" />;
      case 'generated':
        return <Clock className="h-3 w-3" />;
      default:
        return <AlertCircle className="h-3 w-3" />;
    }
  };

  const handlePreview = () => {
    const params = new URLSearchParams({
      subject: pkg.subject,
      unit: pkg.unit
    });
    router.push(`/review/${pkg.id}?${params}`);
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this content package? This action cannot be undone.')) {
      return;
    }

    setIsDeleting(true);
    try {
      if (onDelete) {
        await onDelete(pkg.id);
      }
    } catch (error) {
      console.error('Failed to delete package:', error);
      alert('Failed to delete package. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDuplicate = () => {
    if (onDuplicate) {
      onDuplicate(pkg);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / (1000 * 60));
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

      if (diffMins < 1) return 'just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      
      // For older dates, show the actual date
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      });
    } catch {
      return 'Unknown';
    }
  };

  const getGenerationTime = () => {
    const ms = pkg.generation_metadata?.generation_time_ms;
    if (!ms) return 'Unknown';
    
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${seconds}s`;
  };

  const getCoherenceScore = () => {
    const score = pkg.generation_metadata?.coherence_score;
    if (typeof score !== 'number') return null;
    return Math.round(score * 100);
  };

  return (
    <Card className="hover:shadow-lg transition-shadow duration-200 h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <Badge variant={getStatusVariant(pkg.status || 'generated')} className="flex items-center gap-1">
              {getStatusIcon(pkg.status || 'generated')}
              {pkg.status || 'generated'}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {pkg.subject}
            </Badge>
          </div>
          <div className="text-xs text-muted-foreground">
            ID: {pkg.id.slice(-8)}
          </div>
        </div>
        
        <CardTitle className="line-clamp-2 text-lg leading-tight">
          {pkg.skill} - {pkg.subskill}
        </CardTitle>
        
        <CardDescription className="line-clamp-1">
          {pkg.unit} • Generated {formatDate(pkg.created_at)}
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 space-y-4">
        {/* Content Components Grid */}
        <div>
          <div className="text-sm font-medium mb-2 flex items-center justify-between">
            <span>Components</span>
            <span className="text-xs text-muted-foreground">4/4 complete</span>
          </div>
          
          <div className="grid grid-cols-4 gap-2">
            <div className="flex flex-col items-center p-3 bg-blue-50 rounded-md border">
              <FileText className="h-4 w-4 mb-1 text-blue-600" />
              <span className="text-xs font-medium">Reading</span>
              {pkg.content?.reading && (
                <span className="text-xs text-muted-foreground">
                  {pkg.content.reading.word_count || 0}w
                </span>
              )}
            </div>
            
            <div className="flex flex-col items-center p-3 bg-green-50 rounded-md border">
              <Eye className="h-4 w-4 mb-1 text-green-600" />
              <span className="text-xs font-medium">Visual</span>
              <span className="text-xs text-muted-foreground">p5.js</span>
            </div>
            
            <div className="flex flex-col items-center p-3 bg-purple-50 rounded-md border">
              <Volume2 className="h-4 w-4 mb-1 text-purple-600" />
              <span className="text-xs font-medium">Audio</span>
              {pkg.content?.audio && (
                <span className="text-xs text-muted-foreground">
                  {Math.round((pkg.content.audio.duration_seconds || 0) / 60)}m
                </span>
              )}
            </div>
            
            <div className="flex flex-col items-center p-3 bg-orange-50 rounded-md border">
              <BookOpen className="h-4 w-4 mb-1 text-orange-600" />
              <span className="text-xs font-medium">Practice</span>
              {pkg.content?.practice && (
                <span className="text-xs text-muted-foreground">
                  {pkg.content.practice.problem_count || 0}q
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Metadata */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Generation Time:</span>
            <span className="font-medium">{getGenerationTime()}</span>
          </div>
          
          {getCoherenceScore() !== null && (
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Coherence Score:</span>
              <span className={`font-medium ${
                getCoherenceScore()! >= 90 ? 'text-green-600' : 
                getCoherenceScore()! >= 75 ? 'text-yellow-600' : 'text-red-600'
              }`}>
                {getCoherenceScore()}%
              </span>
            </div>
          )}

          {pkg.master_context?.difficulty_level && (
            <div className="flex justify-between text-xs">
              <span className="text-muted-foreground">Difficulty:</span>
              <span className="font-medium capitalize">
                {pkg.master_context.difficulty_level}
              </span>
            </div>
          )}
        </div>

        {/* Prerequisites */}
        {pkg.master_context?.prerequisites && pkg.master_context.prerequisites.length > 0 && (
          <div>
            <div className="text-xs font-medium mb-1">Prerequisites:</div>
            <div className="flex flex-wrap gap-1">
              {pkg.master_context.prerequisites.slice(0, 3).map(prereq => (
                <Badge key={prereq} variant="outline" className="text-xs px-2 py-0">
                  {prereq.replace('_', ' ')}
                </Badge>
              ))}
              {pkg.master_context.prerequisites.length > 3 && (
                <Badge variant="outline" className="text-xs px-2 py-0">
                  +{pkg.master_context.prerequisites.length - 3}
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex justify-between pt-4">
        <Button variant="outline" size="sm" onClick={handlePreview}>
          <Eye className="mr-2 h-4 w-4" />
          Review
        </Button>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={handlePreview}>
              <Pencil className="mr-2 h-4 w-4" />
              Review Content
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleDuplicate}>
              <Copy className="mr-2 h-4 w-4" />
              Duplicate Package
            </DropdownMenuItem>
            <DropdownMenuItem 
              onClick={handleDelete} 
              disabled={isDeleting}
              className="text-red-600 focus:text-red-600"
            >
              <Trash className="mr-2 h-4 w-4" />
              {isDeleting ? 'Deleting...' : 'Delete Package'}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardFooter>
    </Card>
  );
}