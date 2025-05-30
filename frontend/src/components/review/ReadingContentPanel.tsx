// src/components/review/ReadingContentPanel.tsx - Updated with Revision Support
'use client';

import { useState } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { FileText, MessageSquare, Check, ChevronDown, ChevronUp, RotateCcw } from 'lucide-react';
import { RevisionDialog } from '../RevisionDialog';
import { ReadingContent } from '@/lib/types';

interface ReadingContentPanelProps {
  content: ReadingContent;
  packageId: string;
  subject: string;
  unit: string;
  onRevisionRequest?: (feedback: string, priority: 'low' | 'medium' | 'high') => void;
  isSubmittingRevision?: boolean;
}

export function ReadingContentPanel({ 
  content, 
  packageId, 
  subject, 
  unit, 
  onRevisionRequest,
  isSubmittingRevision = false 
}: ReadingContentPanelProps) {
  const [approved, setApproved] = useState(false);
  const [expandedSections, setExpandedSections] = useState<number[]>([0]); // First section expanded by default
  const [showAllContent, setShowAllContent] = useState(false);
  const [showRevisionDialog, setShowRevisionDialog] = useState(false);

  const handleRevisionRequest = (feedback: string, priority: 'low' | 'medium' | 'high') => {
    if (onRevisionRequest) {
      onRevisionRequest(feedback, priority);
    }
  };

  const toggleSection = (index: number) => {
    setExpandedSections(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const toggleAllSections = () => {
    if (expandedSections.length === content.sections?.length) {
      setExpandedSections([]);
    } else {
      setExpandedSections(content.sections?.map((_, i) => i) || []);
    }
  };

  const getReadingLevelColor = (level: string) => {
    const lowerLevel = level.toLowerCase();
    if (lowerLevel.includes('beginner') || lowerLevel.includes('elementary')) return 'bg-green-100 text-green-800';
    if (lowerLevel.includes('intermediate') || lowerLevel.includes('middle')) return 'bg-yellow-100 text-yellow-800';
    if (lowerLevel.includes('advanced') || lowerLevel.includes('high')) return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <>
      <Card className="h-full flex flex-col">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Reading Content
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline">
                {content.word_count || 0} words
              </Badge>
              <Badge className={getReadingLevelColor(content.reading_level || 'Unknown')}>
                {content.reading_level || 'Unknown Level'}
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="flex-1 overflow-y-auto">
          <div className="space-y-4">
            {/* Title */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-lg text-blue-900 mb-2">
                {content.title || 'Untitled Content'}
              </h3>
              <div className="flex items-center justify-between">
                <span className="text-sm text-blue-700">
                  {content.sections?.length || 0} sections
                </span>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={toggleAllSections}
                  className="text-blue-700 hover:text-blue-800"
                >
                  {expandedSections.length === content.sections?.length ? 'Collapse All' : 'Expand All'}
                </Button>
              </div>
            </div>

            {/* Content Sections */}
            <div className="space-y-3">
              {content.sections?.map((section, index) => (
                <div key={index} className="border rounded-lg">
                  <Collapsible 
                    open={expandedSections.includes(index)}
                    onOpenChange={() => toggleSection(index)}
                  >
                    <CollapsibleTrigger asChild>
                      <Button 
                        variant="ghost" 
                        className="w-full justify-between p-4 h-auto"
                      >
                        <div className="text-left">
                          <h4 className="font-medium text-base mb-1">{section.heading}</h4>
                          <p className="text-sm text-muted-foreground">
                            {section.content?.substring(0, 100)}...
                          </p>
                        </div>
                        {expandedSections.includes(index) ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </CollapsibleTrigger>
                    
                    <CollapsibleContent>
                      <div className="px-4 pb-4 border-t bg-gray-50">
                        <div className="pt-4 space-y-3">
                          {/* Section Content */}
                          <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-2">Content:</h5>
                            <div className="bg-white p-3 rounded border text-sm leading-relaxed">
                              {showAllContent ? section.content : `${section.content?.substring(0, 300)}...`}
                              {section.content && section.content.length > 300 && (
                                <Button 
                                  variant="link" 
                                  size="sm" 
                                  className="p-0 h-auto text-blue-600"
                                  onClick={() => setShowAllContent(!showAllContent)}
                                >
                                  {showAllContent ? 'Show less' : 'Read more'}
                                </Button>
                              )}
                            </div>
                          </div>

                          {/* Key Terms */}
                          {section.key_terms_used && section.key_terms_used.length > 0 && (
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-2">Key Terms Used:</h5>
                              <div className="flex flex-wrap gap-1">
                                {section.key_terms_used.map(term => (
                                  <Badge key={term} variant="secondary" className="text-xs">
                                    {term}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Concepts Covered */}
                          {section.concepts_covered && section.concepts_covered.length > 0 && (
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-2">Concepts Covered:</h5>
                              <div className="flex flex-wrap gap-1">
                                {section.concepts_covered.map(concept => (
                                  <Badge key={concept} variant="outline" className="text-xs">
                                    {concept}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                </div>
              )) || (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No reading content available</p>
                </div>
              )}
            </div>

            {/* Content Analysis */}
            <div className="bg-gray-50 rounded-lg p-4 space-y-2">
              <h5 className="font-medium text-sm">Content Analysis:</h5>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Word Count:</span>
                  <span className="ml-2 font-medium">{content.word_count || 0}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Reading Level:</span>
                  <span className="ml-2 font-medium">{content.reading_level || 'Unknown'}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Sections:</span>
                  <span className="ml-2 font-medium">{content.sections?.length || 0}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Est. Read Time:</span>
                  <span className="ml-2 font-medium">
                    {Math.ceil((content.word_count || 0) / 200)} min
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
        componentType="reading"
        onSubmit={handleRevisionRequest}
        isSubmitting={isSubmittingRevision}
      />
    </>
  );
}