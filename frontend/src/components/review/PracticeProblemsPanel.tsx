// src/components/review/PracticeProblemsPanel.tsx
'use client';

import { useState } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { BookOpen, Plus, Check, ChevronDown, MessageSquare, Clock, Target, Lightbulb } from 'lucide-react';
import { PracticeContent } from '@/lib/types';

interface PracticeProblemsPanelProps {
  content: PracticeContent;
}

export function PracticeProblemsPanel({ content }: PracticeProblemsPanelProps) {
  const [approved, setApproved] = useState(false);
  const [expandedProblems, setExpandedProblems] = useState<number[]>([0]); // First problem expanded by default

  const toggleProblem = (index: number) => {
    setExpandedProblems(prev => 
      prev.includes(index) 
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const toggleAllProblems = () => {
    if (expandedProblems.length === content.problems?.length) {
      setExpandedProblems([]);
    } else {
      setExpandedProblems(content.problems?.map((_, i) => i) || []);
    }
  };

  const getDifficultyColor = (difficulty: number) => {
    if (difficulty <= 3) return 'bg-green-100 text-green-800';
    if (difficulty <= 6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getDifficultyLabel = (difficulty: number) => {
    if (difficulty <= 3) return 'Easy';
    if (difficulty <= 6) return 'Medium';
    return 'Hard';
  };

  const getProblemTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'multiple choice':
        return '📝';
      case 'fill in the blank':
        return '✏️';
      case 'true/false':
        return '✅';
      case 'numerical':
        return '🔢';
      case 'essay':
        return '📄';
      default:
        return '❓';
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Practice Problems
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {content.problem_count || content.problems?.length || 0} problems
            </Badge>
            <Badge variant="outline" className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {content.estimated_time_minutes || 0}m
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto">
        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-orange-900">Problem Set Overview</h4>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={toggleAllProblems}
                className="text-orange-700 hover:text-orange-800"
              >
                {expandedProblems.length === content.problems?.length ? 'Collapse All' : 'Expand All'}
              </Button>
            </div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="text-center">
                <div className="font-semibold text-orange-900">{content.problems?.length || 0}</div>
                <div className="text-orange-700">Total Problems</div>
              </div>
              <div className="text-center">
                <div className="font-semibold text-orange-900">{content.estimated_time_minutes || 0}</div>
                <div className="text-orange-700">Est. Minutes</div>
              </div>
              <div className="text-center">
                <div className="font-semibold text-orange-900">
                  {content.problems ? 
                    Math.round(content.problems.reduce((sum, p) => sum + p.difficulty, 0) / content.problems.length) 
                    : 0}/10
                  </div>
                <div className="text-orange-700">Avg Difficulty</div>
              </div>
            </div>
          </div>

          {/* Problems List */}
          <div className="space-y-3">
            {content.problems?.map((problem, index) => (
              <Card key={problem.id || index} className="border-l-4 border-l-orange-500">
                <Collapsible 
                  open={expandedProblems.includes(index)}
                  onOpenChange={() => toggleProblem(index)}
                >
                  <CollapsibleTrigger asChild>
                    <Button 
                      variant="ghost" 
                      className="w-full justify-between p-4 h-auto"
                    >
                      <div className="flex items-center gap-3 text-left">
                        <span className="text-lg">{getProblemTypeIcon(problem.problem_data.problem_type)}</span>
                        <div>
                          <div className="font-medium">
                            Problem {index + 1}: {problem.problem_data.problem_type}
                          </div>
                          <div className="text-sm text-muted-foreground line-clamp-1">
                            {problem.problem_data.problem}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={getDifficultyColor(problem.difficulty)}>
                          {getDifficultyLabel(problem.difficulty)}
                        </Badge>
                        <ChevronDown className={`h-4 w-4 transform transition-transform ${
                          expandedProblems.includes(index) ? 'rotate-180' : ''
                        }`} />
                      </div>
                    </Button>
                  </CollapsibleTrigger>
                  
                  <CollapsibleContent>
                    <div className="px-4 pb-4 border-t bg-gray-50">
                      <div className="pt-4 space-y-4">
                        {/* Problem Statement */}
                        <div>
                          <h5 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                            <Target className="h-4 w-4" />
                            Problem Statement:
                          </h5>
                          <div className="bg-white p-3 rounded border">
                            <p className="text-sm leading-relaxed">
                              {problem.problem_data.problem}
                            </p>
                          </div>
                        </div>

                        {/* Answer */}
                        <div>
                          <h5 className="text-sm font-medium text-green-700 mb-2">
                            ✅ Correct Answer:
                          </h5>
                          <div className="bg-green-50 border border-green-200 p-3 rounded">
                            <p className="text-sm font-medium text-green-800">
                              {problem.problem_data.answer}
                            </p>
                          </div>
                        </div>

                        {/* Success Criteria */}
                        {problem.problem_data.success_criteria && 
                         problem.problem_data.success_criteria.length > 0 && (
                          <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-2">
                              Success Criteria:
                            </h5>
                            <div className="bg-white border rounded p-3">
                              <ul className="text-sm space-y-1">
                                {problem.problem_data.success_criteria.map((criteria, idx) => (
                                  <li key={idx} className="flex items-start gap-2">
                                    <span className="text-blue-600 mt-0.5">•</span>
                                    <span>{criteria}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        )}

                        {/* Teaching Note */}
                        {problem.problem_data.teaching_note && (
                          <div>
                            <h5 className="text-sm font-medium text-purple-700 mb-2 flex items-center gap-2">
                              <Lightbulb className="h-4 w-4" />
                              Teaching Note:
                            </h5>
                            <div className="bg-purple-50 border border-purple-200 p-3 rounded">
                              <p className="text-sm text-purple-800">
                                {problem.problem_data.teaching_note}
                              </p>
                            </div>
                          </div>
                        )}

                        {/* Problem Metadata */}
                        {problem.problem_data.metadata && (
                          <div className="bg-gray-100 rounded p-3">
                            <h5 className="text-xs font-medium text-gray-600 mb-2">Problem Metadata:</h5>
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              <div>
                                <span className="text-gray-500">Subject:</span>
                                <span className="ml-1 font-medium">{problem.problem_data.metadata.subject}</span>
                              </div>
                              <div>
                                <span className="text-gray-500">Unit:</span>
                                <span className="ml-1 font-medium">{problem.problem_data.metadata.unit?.title}</span>
                              </div>
                              <div>
                                <span className="text-gray-500">Skill:</span>
                                <span className="ml-1 font-medium">{problem.problem_data.metadata.skill?.description}</span>
                              </div>
                              <div>
                                <span className="text-gray-500">Difficulty:</span>
                                <span className="ml-1 font-medium">{problem.difficulty}/10</span>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </CollapsibleContent>
                </Collapsible>
              </Card>
            )) || (
              <div className="text-center py-8 text-muted-foreground">
                <BookOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No practice problems available</p>
              </div>
            )}
          </div>

          {/* Problem Set Analysis */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-3">
            <h5 className="font-medium text-sm">Problem Set Analysis:</h5>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Total Problems:</span>
                <span className="ml-2 font-medium">{content.problems?.length || 0}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Est. Time:</span>
                <span className="ml-2 font-medium">{content.estimated_time_minutes || 0} min</span>
              </div>
              <div>
                <span className="text-muted-foreground">Avg Difficulty:</span>
                <span className="ml-2 font-medium">
                  {content.problems && content.problems.length > 0 ? 
                    (content.problems.reduce((sum, p) => sum + p.difficulty, 0) / content.problems.length).toFixed(1)
                    : 0}/10
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Problem Types:</span>
                <span className="ml-2 font-medium">
                  {content.problems ? 
                    [...new Set(content.problems.map(p => p.problem_data.problem_type))].length
                    : 0}
                </span>
              </div>
            </div>

            {/* Difficulty Distribution */}
            {content.problems && content.problems.length > 0 && (
              <div>
                <span className="text-sm text-muted-foreground">Difficulty Distribution:</span>
                <div className="flex gap-2 mt-1">
                  {['Easy', 'Medium', 'Hard'].map(level => {
                    const count = content.problems!.filter(p => {
                      if (level === 'Easy') return p.difficulty <= 3;
                      if (level === 'Medium') return p.difficulty > 3 && p.difficulty <= 6;
                      return p.difficulty > 6;
                    }).length;
                    
                    return (
                      <Badge key={level} variant="outline" className="text-xs">
                        {level}: {count}
                      </Badge>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex justify-between border-t">
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <MessageSquare className="mr-2 h-4 w-4" />
            Add Note
          </Button>
          <Button variant="outline" size="sm">
            <Plus className="mr-2 h-4 w-4" />
            Add Problem
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
  );
}