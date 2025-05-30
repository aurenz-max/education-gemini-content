// components/RevisionDialog.tsx
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Loader2, MessageSquare, AlertCircle } from 'lucide-react';
import { ComponentType } from '@/lib/types';

interface RevisionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  componentType: ComponentType;
  onSubmit: (feedback: string, priority: 'low' | 'medium' | 'high') => void;
  isSubmitting?: boolean;
}

export function RevisionDialog({ 
  isOpen, 
  onClose, 
  componentType, 
  onSubmit,
  isSubmitting = false 
}: RevisionDialogProps) {
  const [feedback, setFeedback] = useState('');
  const [priority, setPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [selectedSuggestion, setSelectedSuggestion] = useState<string>('');

  const handleSubmit = () => {
    if (feedback.trim()) {
      onSubmit(feedback, priority);
      handleClose();
    }
  };

  const handleClose = () => {
    setFeedback('');
    setPriority('medium');
    setSelectedSuggestion('');
    onClose();
  };

  const getPlaceholderText = (componentType: ComponentType): string => {
    const placeholders = {
      reading: "e.g., 'Make less technical, add more examples for beginners'",
      visual: "e.g., 'Add more interactive elements, make sliders more prominent'", 
      audio: "e.g., 'Make dialogue more conversational, add student questions'",
      practice: "e.g., 'Add 2 more problems, make first few easier'"
    };
    return placeholders[componentType] || "Describe the changes needed...";
  };

  const getFeedbackSuggestions = (componentType: ComponentType): string[] => {
    const suggestions = {
      reading: [
        "Make less technical for beginners",
        "Add more real-world examples", 
        "Shorten the explanations",
        "Add step-by-step breakdown",
        "Include more visual descriptions",
        "Simplify vocabulary"
      ],
      visual: [
        "Add more interactive elements",
        "Make labels clearer",
        "Add animation to show change",
        "Include reset button",
        "Add color coding",
        "Make it more responsive"
      ],
      audio: [
        "Make more conversational",
        "Add student questions",
        "Slow down the pace",
        "Include more examples",
        "Add pauses for thinking",
        "Make voices more distinct"
      ],
      practice: [
        "Add more problems",
        "Make first problems easier", 
        "Include worked examples",
        "Add hint system",
        "Provide better feedback",
        "Include scaffolding"
      ]
    };
    return suggestions[componentType] || [];
  };

  const getComponentIcon = (componentType: ComponentType): string => {
    const icons = {
      reading: "📖",
      visual: "🎨", 
      audio: "🎧",
      practice: "📝"
    };
    return icons[componentType];
  };

  const suggestions = getFeedbackSuggestions(componentType);

  const handleSuggestionClick = (suggestion: string) => {
    setSelectedSuggestion(suggestion);
    setFeedback(suggestion);
  };

  const getPriorityColor = (p: string) => {
    switch (p) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="text-xl">{getComponentIcon(componentType)}</span>
            Request Changes - {componentType.charAt(0).toUpperCase() + componentType.slice(1)} Content
          </DialogTitle>
          <DialogDescription>
            Describe what changes you'd like made to this component. Be specific to help the AI understand your requirements.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* Quick Suggestions */}
          <div>
            <Label className="text-sm font-medium mb-3 block">Common Suggestions:</Label>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((suggestion, index) => (
                <Button
                  key={index}
                  variant={selectedSuggestion === suggestion ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-xs"
                >
                  {suggestion}
                </Button>
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Click a suggestion to use it, or write your own feedback below
            </p>
          </div>

          {/* Custom Feedback */}
          <div>
            <Label htmlFor="feedback" className="text-sm font-medium">
              Detailed Feedback <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="feedback"
              placeholder={getPlaceholderText(componentType)}
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={4}
              className="mt-1"
            />
            <div className="flex justify-between items-center mt-1">
              <p className="text-xs text-muted-foreground">
                Be specific about what needs to change and why
              </p>
              <span className="text-xs text-muted-foreground">
                {feedback.length}/500
              </span>
            </div>
          </div>
          
          {/* Priority Selection */}
          <div>
            <Label htmlFor="priority" className="text-sm font-medium">Priority Level</Label>
            <Select value={priority} onValueChange={(value: 'low' | 'medium' | 'high') => setPriority(value)}>
              <SelectTrigger className="mt-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-green-100 text-green-800 text-xs">Low</Badge>
                    <span>Minor improvements</span>
                  </div>
                </SelectItem>
                <SelectItem value="medium">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-yellow-100 text-yellow-800 text-xs">Medium</Badge>
                    <span>Important changes</span>
                  </div>
                </SelectItem>
                <SelectItem value="high">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-red-100 text-red-800 text-xs">High</Badge>
                    <span>Critical revisions needed</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Information Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex gap-3">
              <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium text-blue-900 mb-1">Revision Process:</p>
                <ul className="text-blue-800 space-y-1 text-xs">
                  <li>• Your feedback will be processed by AI to revise this component</li>
                  <li>• Other components will remain unchanged unless they need updating for coherence</li>
                  <li>• The revised package will be available for review in 1-2 minutes</li>
                  <li>• You can track revision progress in the package status</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        
        <DialogFooter>
          <Button 
            variant="outline" 
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!feedback.trim() || isSubmitting}
            className="min-w-[120px]"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <MessageSquare className="mr-2 h-4 w-4" />
                Request Revision
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}