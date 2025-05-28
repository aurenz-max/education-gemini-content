// src/app/generate/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ContentGenerationForm } from '@/components/ContentGenerationForm';
import { GenerationProgress } from '@/components/GenerationProgress';
import { useContent } from '@/lib/context';
import { GenerationRequest } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Home } from 'lucide-react';

export default function GeneratePage() {
  const router = useRouter();
  const { generateContent, error, clearError } = useContent();
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentGeneration, setCurrentGeneration] = useState<{
    packageId: string;
    subject: string;
    unit: string;
    skill: string;
    subskill: string;
  } | null>(null);

  const handleGenerateContent = async (request: GenerationRequest) => {
    try {
      setIsGenerating(true);
      clearError();
      
      console.log('Starting content generation with request:', request);
      
      const packageId = await generateContent(request);
      
      console.log('Content generation started, package ID:', packageId);
      
      // Set up progress tracking
      setCurrentGeneration({
        packageId,
        subject: request.subject,
        unit: request.unit,
        skill: request.skill,
        subskill: request.subskill
      });
      
    } catch (err) {
      console.error('Content generation failed:', err);
      setIsGenerating(false);
      // Error is handled by the context
    }
  };

  const handleGenerationComplete = (packageId: string) => {
    console.log('Generation completed for package:', packageId);
    setIsGenerating(false);
    // Could show success notification here
  };

  const startNewGeneration = () => {
    setCurrentGeneration(null);
    setIsGenerating(false);
    clearError();
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
            variant="outline" 
            onClick={() => router.push('/library')}
            className="flex items-center gap-2"
          >
            <Home className="h-4 w-4" />
            View Library
          </Button>
        </div>
        
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight mb-4">
            Generate Educational Content
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Create comprehensive learning materials with AI-powered content generation. 
            Each package includes reading, visual, audio, and practice components.
          </p>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="max-w-2xl mx-auto mb-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium text-red-800">Generation Failed</h3>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
              <Button variant="outline" size="sm" onClick={clearError}>
                Dismiss
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      {currentGeneration ? (
        <div className="space-y-6">
          <GenerationProgress
            packageId={currentGeneration.packageId}
            subject={currentGeneration.subject}
            unit={currentGeneration.unit}
            skill={currentGeneration.skill}
            subskill={currentGeneration.subskill}
            onComplete={handleGenerationComplete}
          />
          
          {/* Start New Generation Button */}
          <div className="text-center">
            <Button 
              variant="outline" 
              onClick={startNewGeneration}
              className="mt-4"
            >
              Generate Another Package
            </Button>
          </div>
        </div>
      ) : (
        <ContentGenerationForm 
          onSubmit={handleGenerateContent}
          loading={isGenerating}
        />
      )}

      {/* Help Section */}
      <div className="max-w-4xl mx-auto mt-12">
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">How Content Generation Works</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium mb-2">📝 What You Provide</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Subject area (e.g., Mathematics)</li>
                <li>• Unit topic (e.g., Algebra)</li>
                <li>• Specific skill (e.g., Linear Equations)</li>
                <li>• Subskill focus (e.g., Slope-Intercept Form)</li>
                <li>• Difficulty level and prerequisites</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">🎯 What You Get</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Structured reading content with key concepts</li>
                <li>• Interactive p5.js visual demonstration</li>
                <li>• Teacher-student audio dialogue</li>
                <li>• Practice problems with teaching notes</li>
                <li>• All content aligned to learning objectives</li>
              </ul>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Pro Tip:</strong> Be specific with your subskill to get the most targeted content. 
              For example, "Slope-Intercept Form" is better than just "Linear Equations."
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}