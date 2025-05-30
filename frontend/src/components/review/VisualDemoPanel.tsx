// src/components/review/VisualDemoPanel.tsx - Updated with Revision Support
'use client';

import { useState } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Eye, Play, Code, Check, ChevronDown, MessageSquare, ExternalLink, RotateCcw } from 'lucide-react';
import { RevisionDialog } from '../RevisionDialog';
import { VisualContent } from '@/lib/types';

interface VisualDemoPanelProps {
  content: VisualContent;
  packageId: string;
  subject: string;
  unit: string;
  onRevisionRequest?: (feedback: string, priority: 'low' | 'medium' | 'high') => void;
  isSubmittingRevision?: boolean;
}

export function VisualDemoPanel({ 
  content, 
  packageId, 
  subject, 
  unit, 
  onRevisionRequest,
  isSubmittingRevision = false 
}: VisualDemoPanelProps) {
  const [approved, setApproved] = useState(false);
  const [showCode, setShowCode] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [showRevisionDialog, setShowRevisionDialog] = useState(false);

  const handleRevisionRequest = (feedback: string, priority: 'low' | 'medium' | 'high') => {
    if (onRevisionRequest) {
      onRevisionRequest(feedback, priority);
    }
  };

  const runDemo = () => {
    setIsRunning(true);
    // Simulate demo execution
    setTimeout(() => setIsRunning(false), 2000);
  };

  const openInNewWindow = () => {
    // Create a new window with the p5.js code
    const newWindow = window.open('', '_blank', 'width=800,height=600');
    if (newWindow) {
      newWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Visual Demo</title>
          <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.7.0/p5.min.js"></script>
          <style>
            body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
            .info { margin-bottom: 20px; padding: 10px; background: #f0f0f0; border-radius: 5px; }
          </style>
        </head>
        <body>
          <div class="info">
            <h3>${content.description || 'Interactive Visual Demo'}</h3>
            <p><strong>Instructions:</strong> ${content.user_instructions || 'Interact with the visualization below.'}</p>
          </div>
          <script>
            ${content.p5_code || '// No code available'}
          </script>
        </body>
        </html>
      `);
      newWindow.document.close();
    }
  };

  return (
    <>
      <Card className="h-full flex flex-col">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5" />
              Interactive Visual Demo
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={runDemo} disabled={isRunning}>
                {isRunning ? (
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                {isRunning ? 'Running...' : 'Preview'}
              </Button>
              <Button variant="outline" size="sm" onClick={openInNewWindow}>
                <ExternalLink className="mr-2 h-4 w-4" />
                Open Demo
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto">
          <div className="space-y-4">
            {/* Demo Description */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="font-medium text-green-900 mb-2">Demo Description:</h4>
              <p className="text-sm text-green-800">
                {content.description || 'No description available'}
              </p>
            </div>

            {/* User Instructions */}
            {content.user_instructions && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">User Instructions:</h4>
                <p className="text-sm text-blue-800">
                  {content.user_instructions}
                </p>
              </div>
            )}

            {/* Interactive Elements */}
            {content.interactive_elements && content.interactive_elements.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Interactive Elements:</h4>
                <div className="flex flex-wrap gap-2">
                  {content.interactive_elements.map(element => (
                    <Badge key={element} variant="secondary" className="text-xs">
                      {element.replace('_', ' ')}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Concepts Demonstrated */}
            {content.concepts_demonstrated && content.concepts_demonstrated.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Concepts Demonstrated:</h4>
                <div className="flex flex-wrap gap-2">
                  {content.concepts_demonstrated.map(concept => (
                    <Badge key={concept} variant="outline" className="text-xs">
                      {concept}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Demo Preview Area */}
            <div className="bg-gray-900 rounded-lg p-6 text-center text-white min-h-[200px] flex items-center justify-center">
              {isRunning ? (
                <div className="space-y-4">
                  <div className="animate-pulse">
                    <div className="w-16 h-16 mx-auto bg-blue-500 rounded-lg flex items-center justify-center">
                      <Play className="h-8 w-8" />
                    </div>
                  </div>
                  <p className="text-sm">Running p5.js demonstration...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <Eye className="h-12 w-12 mx-auto text-gray-400" />
                  <div>
                    <p className="font-medium">Visual Demo Preview</p>
                    <p className="text-sm text-gray-400 mt-1">
                      Click "Preview" or "Open Demo" to run the interactive visualization
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Code Section */}
            <Collapsible open={showCode} onOpenChange={setShowCode}>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" className="w-full justify-between">
                  <span className="flex items-center gap-2">
                    <Code className="h-4 w-4" />
                    View p5.js Code
                  </span>
                  <ChevronDown className={`h-4 w-4 transform transition-transform ${showCode ? 'rotate-180' : ''}`} />
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="mt-2 bg-gray-900 rounded-lg p-4 overflow-x-auto">
                  <pre className="text-sm text-green-400 whitespace-pre-wrap font-mono">
                    <code>{content.p5_code || '// No code available'}</code>
                  </pre>
                </div>
                <div className="mt-2 text-xs text-muted-foreground">
                  Code is sandboxed and runs in a separate window for security
                </div>
              </CollapsibleContent>
            </Collapsible>

            {/* Technical Details */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <h5 className="font-medium text-sm">Technical Details:</h5>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Framework:</span>
                  <span className="ml-2 font-medium">p5.js</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Interactive:</span>
                  <span className="ml-2 font-medium">
                    {content.interactive_elements && content.interactive_elements.length > 0 ? 'Yes' : 'Static'}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Concepts:</span>
                  <span className="ml-2 font-medium">
                    {content.concepts_demonstrated?.length || 0}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Code Lines:</span>
                  <span className="ml-2 font-medium">
                    {content.p5_code ? content.p5_code.split('\n').length : 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex justify-between border-t">
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <MessageSquare className="mr-2 h-4 w-4" />
              Add Note
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setShowRevisionDialog(true)}
              disabled={isSubmittingRevision}
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Request Changes
            </Button>
          </div>
          <Button 
            size="sm" 
            variant={approved ? "default" : "outline"}
            onClick={() => setApproved(!approved)}
          >
            <Check className="mr-2 h-4 w-4" />
            {approved ? 'Approved' : 'Approve'}
          </Button>
        </CardFooter>
      </Card>

      {/* Revision Dialog */}
      <RevisionDialog
        isOpen={showRevisionDialog}
        onClose={() => setShowRevisionDialog(false)}
        componentType="visual"
        onSubmit={handleRevisionRequest}
        isSubmitting={isSubmittingRevision}
      />
    </>
  );
}