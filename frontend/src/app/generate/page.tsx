// src/app/generate/page.tsx - Updated with Enhanced Generation
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { GenerationProgress } from '@/components/GenerationProgress';
import { EnhancedContentGenerationRequest } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Home } from 'lucide-react';
import { contentAPI } from '@/lib/api';
import dynamic from 'next/dynamic';

// Dynamically import the enhanced form to avoid SSR issues with complex state
const EnhancedContentGenerationForm = dynamic(
  () => import('@/components/ContentGenerationForm'),
  { ssr: false }
);

export default function GeneratePage() {
  const router = useRouter();
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentGeneration, setCurrentGeneration] = useState<{
    packageId: string;
    subject: string;
    unit: string;
    skill: string;
    subskill: string;
    grade?: string;
  } | null>(null);

  const handleGenerateContent = async (request: EnhancedContentGenerationRequest) => {
    try {
      setIsGenerating(true);
      setError(null);
      
      console.log('Starting enhanced content generation with request:', request);
      
      // Use the enhanced generation endpoint
      const contentPackage = await contentAPI.generateContentEnhanced(request);
      
      console.log('Content generation started, package:', contentPackage);
      
      // Set up progress tracking with enhanced metadata
      setCurrentGeneration({
        packageId: contentPackage.id,
        subject: contentPackage.subject,
        unit: contentPackage.unit,
        skill: contentPackage.skill,
        subskill: contentPackage.subskill,
        grade: contentPackage.grade
      });
      
    } catch (err) {
      console.error('Enhanced content generation failed:', err);
      setIsGenerating(false);
      setError(err instanceof Error ? err.message : 'Content generation failed');
    }
  };

  const handleGenerationComplete = (packageId: string) => {
    console.log('Generation completed for package:', packageId);
    setIsGenerating(false);
  };

  const startNewGeneration = () => {
    setCurrentGeneration(null);
    setIsGenerating(false);
    setError(null);
  };

  const clearError = () => {
    setError(null);
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
            Enhanced Content Generation
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Generate grade-appropriate learning materials from curriculum data or custom input. 
            Browse your curriculum structure or manually specify learning objectives.
          </p>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="max-w-4xl mx-auto mb-6">
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
          
          {/* Generation Info Panel */}
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg border shadow-sm p-6">
              <h3 className="font-medium mb-4">Generation Details</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Subject:</span>
                  <p className="font-medium">{currentGeneration.subject}</p>
                </div>
                {currentGeneration.grade && (
                  <div>
                    <span className="text-muted-foreground">Grade:</span>
                    <p className="font-medium">{currentGeneration.grade}</p>
                  </div>
                )}
                <div>
                  <span className="text-muted-foreground">Unit:</span>
                  <p className="font-medium">{currentGeneration.unit}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Skill:</span>
                  <p className="font-medium">{currentGeneration.skill}</p>
                </div>
                <div className="col-span-2">
                  <span className="text-muted-foreground">Subskill:</span>
                  <p className="font-medium">{currentGeneration.subskill}</p>
                </div>
              </div>
            </div>
          </div>
          
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
        <EnhancedContentGenerationForm 
          onSubmit={handleGenerateContent}
          loading={isGenerating}
        />
      )}

      {/* Enhanced Help Section */}
      <div className="max-w-4xl mx-auto mt-12">
        <div className="bg-white rounded-lg border shadow-sm p-6">
          <h2 className="text-xl font-semibold mb-4">Enhanced Content Generation Features</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium mb-2">📚 Curriculum Mode</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Browse your loaded curriculum structure</li>
                <li>• Select from organized units, skills, and subskills</li>
                <li>• Auto-populate with curriculum metadata</li>
                <li>• View learning paths and prerequisites</li>
                <li>• Override difficulty and prerequisites as needed</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">✏️ Manual Mode</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Traditional manual entry for custom content</li>
                <li>• Specify grade level for age-appropriate content</li>
                <li>• Full control over difficulty and prerequisites</li>
                <li>• Add custom instructions and requirements</li>
                <li>• Perfect for content outside your curriculum</li>
              </ul>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium mb-2">🎯 Grade-Appropriate Content</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Reading level matched to grade</li>
                <li>• Age-appropriate examples and language</li>
                <li>• Cognitive complexity aligned to developmental stage</li>
                <li>• Visual and audio content optimized for age group</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">🔗 Learning Path Integration</h3>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Prerequisite knowledge automatically included</li>
                <li>• Next steps in learning sequence suggested</li>
                <li>• Cross-curricular connections identified</li>
                <li>• Coherent progression through curriculum</li>
              </ul>
            </div>
          </div>

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Getting Started:</strong> If you have curriculum data loaded, try the Curriculum Mode 
              to browse and select from your existing structure. Otherwise, use Manual Mode with the optional 
              grade field to ensure age-appropriate content generation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}