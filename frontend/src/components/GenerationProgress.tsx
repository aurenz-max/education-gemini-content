// src/components/GenerationProgress.tsx
'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { CheckCircle, Clock, Loader2, RefreshCw, ExternalLink } from 'lucide-react';
import { usePolling } from '@/lib/hooks/usePolling';
import { contentAPI } from '@/lib/api';

interface GenerationProgressProps {
  packageId: string;
  subject: string;
  unit: string;
  skill: string;
  subskill: string;
  onComplete?: (packageId: string) => void;
}

const GENERATION_STAGES = [
  { key: 'master_context', label: 'Master Context', description: 'Creating learning framework' },
  { key: 'reading', label: 'Reading Content', description: 'Generating explanatory text' },
  { key: 'visual', label: 'Visual Demo', description: 'Creating interactive visualization' },
  { key: 'audio_script', label: 'Audio Script', description: 'Writing dialogue content' },
  { key: 'audio_tts', label: 'Audio Generation', description: 'Converting to speech' },
  { key: 'practice', label: 'Practice Problems', description: 'Creating assessment questions' },
  { key: 'validation', label: 'Validation', description: 'Quality checking content' }
];

export function GenerationProgress({ 
  packageId, 
  subject, 
  unit, 
  skill, 
  subskill, 
  onComplete 
}: GenerationProgressProps) {
  const [startTime] = useState(Date.now());
  const [currentStage, setCurrentStage] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Poll for package completion
  const { data: packageData, loading: polling, error: pollError } = usePolling(
    async () => {
      try {
        const pkg = await contentAPI.getContentPackage(packageId, subject, unit);
        return pkg;
      } catch (err) {
        // If package not found, it's still generating
        if (err instanceof Error && err.message.includes('not found')) {
          return null;
        }
        throw err;
      }
    },
    5000, // Poll every 5 seconds
    !isComplete
  );

  // Simulate progress stages
  useEffect(() => {
    if (isComplete) return;

    const interval = setInterval(() => {
      setCurrentStage(prev => {
        if (prev < GENERATION_STAGES.length - 1) {
          return prev + 1;
        }
        return prev;
      });
    }, 20000); // Advance stage every 20 seconds

    return () => clearInterval(interval);
  }, [isComplete]);

  // Check if generation is complete
  useEffect(() => {
    if (packageData && !isComplete) {
      setIsComplete(true);
      setCurrentStage(GENERATION_STAGES.length);
      if (onComplete) {
        onComplete(packageId);
      }
    }
  }, [packageData, isComplete, packageId, onComplete]);

  // Handle polling errors
  useEffect(() => {
    if (pollError) {
      setError(pollError);
    }
  }, [pollError]);

  const getElapsedTime = () => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const getProgressPercentage = () => {
    if (isComplete) return 100;
    return Math.floor((currentStage / GENERATION_STAGES.length) * 100);
  };

  const getCurrentStageInfo = () => {
    if (isComplete) {
      return { label: 'Complete', description: 'Content package ready for review' };
    }
    return GENERATION_STAGES[currentStage] || GENERATION_STAGES[0];
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      {/* Header Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {isComplete ? (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                ) : (
                  <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                )}
                {isComplete ? 'Generation Complete!' : 'Generating Content Package'}
              </CardTitle>
              <CardDescription className="mt-1">
                {subject} → {unit} → {skill} → {subskill}
              </CardDescription>
            </div>
            <div className="text-right">
              <Badge variant={isComplete ? 'default' : 'secondary'}>
                Package ID: {packageId}
              </Badge>
              <div className="text-sm text-muted-foreground mt-1">
                {getElapsedTime()}
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{getProgressPercentage()}%</span>
              </div>
              <Progress value={getProgressPercentage()} className="w-full" />
            </div>

            {/* Current Stage */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-2">
                {isComplete ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <Clock className="h-4 w-4 text-blue-600" />
                )}
                <span className="font-medium text-blue-900">
                  {getCurrentStageInfo().label}
                </span>
              </div>
              <p className="text-sm text-blue-700 mt-1">
                {getCurrentStageInfo().description}
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-sm text-red-700">
                  <strong>Error:</strong> {error}
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Stage Progress */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Generation Stages</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {GENERATION_STAGES.map((stage, index) => (
              <div key={stage.key} className="flex items-center gap-3">
                <div className="flex-shrink-0">
                  {isComplete || index < currentStage ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : index === currentStage ? (
                    <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                  ) : (
                    <div className="h-5 w-5 rounded-full border-2 border-gray-300" />
                  )}
                </div>
                <div className="flex-1">
                  <div className={`font-medium ${
                    isComplete || index <= currentStage 
                      ? 'text-gray-900' 
                      : 'text-gray-500'
                  }`}>
                    {stage.label}
                  </div>
                  <div className={`text-sm ${
                    isComplete || index <= currentStage 
                      ? 'text-gray-600' 
                      : 'text-gray-400'
                  }`}>
                    {stage.description}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button 
          variant="outline" 
          onClick={() => window.location.reload()}
          disabled={polling}
          className="flex-1"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${polling ? 'animate-spin' : ''}`} />
          Refresh Status
        </Button>
        
        {isComplete && (
          <Button 
            onClick={() => window.open(`/review/${packageId}?subject=${subject}&unit=${unit}`, '_blank')}
            className="flex-1"
          >
            <ExternalLink className="mr-2 h-4 w-4" />
            Review Content
          </Button>
        )}
      </div>

      {/* Info Panel */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-2 text-sm text-muted-foreground">
            <p>• Content generation typically takes 2-5 minutes</p>
            <p>• You can navigate away and return to check progress</p>
            <p>• All components are generated with coherent learning objectives</p>
            {isComplete && (
              <p className="text-green-600 font-medium">
                • Your content package is ready for review!
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}