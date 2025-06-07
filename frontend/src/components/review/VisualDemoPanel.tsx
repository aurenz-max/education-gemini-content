import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  Eye, 
  Play, 
  Code, 
  Check, 
  MessageSquare, 
  ExternalLink, 
  RotateCcw, 
  Send,
  Save,
  Download,
  RefreshCw,
  Maximize2,
  Copy,
  Settings,
  Pause,
  Square,
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  Bot,
  User
} from 'lucide-react';

// Using your actual types from the API
interface VisualContent {
  p5_code: string;
  description: string;
  interactive_elements: string[];
  concepts_demonstrated: string[];
  user_instructions: string;
}

interface VisualDemoPanelProps {
  content: VisualContent;
  packageId: string;
  subject: string;
  unit: string;
  onRevisionRequest?: (feedback: string, priority: 'low' | 'medium' | 'high') => void;
  isSubmittingRevision?: boolean;
  onSavePackage?: () => Promise<void>;
  onApprovePackage?: () => Promise<void>;
  packageStatus?: 'draft' | 'generated' | 'approved' | 'rejected' | 'needs_revision' | 'under_review' | 'published';
}

interface ChatMessage {
  id: number;
  type: 'user' | 'assistant';
  message: string;
  timestamp: string;
  priority?: 'low' | 'medium' | 'high';
}

// Export as both named and default for flexibility
export const VisualDemoPanel = ({ 
  content, 
  packageId, 
  subject, 
  unit, 
  onRevisionRequest,
  isSubmittingRevision = false,
  onSavePackage,
  onApprovePackage,
  packageStatus = 'generated'
}: VisualDemoPanelProps) => {
  const [approved, setApproved] = useState(packageStatus === 'approved');
  const [isRunning, setIsRunning] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'success' | 'error' | null>(null);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [selectedPriority, setSelectedPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [activeTab, setActiveTab] = useState('preview');

  // Update approved state when packageStatus changes
  useEffect(() => {
    setApproved(packageStatus === 'approved');
  }, [packageStatus]);

  const runDemo = () => {
    setIsRunning(true);
    setTimeout(() => setIsRunning(false), 2000);
  };

  const openInNewWindow = () => {
    const newWindow = window.open('', '_blank', 'width=900,height=700');
    if (newWindow) {
      newWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Visual Demo - ${content.description || 'Interactive Demo'}</title>
          <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.7.0/p5.min.js"></script>
          <style>
            body { 
              margin: 0; 
              padding: 20px; 
              font-family: Arial, sans-serif; 
              background: #1a1a2e;
              color: white;
            }
            .info { 
              margin-bottom: 20px; 
              padding: 15px; 
              background: rgba(255,255,255,0.1); 
              border-radius: 8px; 
              backdrop-filter: blur(10px);
            }
            h3 { color: #64ffda; margin-top: 0; }
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

  const copyCode = async () => {
    try {
      await navigator.clipboard.writeText(content.p5_code);
      // Could integrate with a toast notification system if available
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  const downloadCode = () => {
    const blob = new Blob([content.p5_code], { type: 'text/javascript' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `visual-demo-${packageId}.js`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleSavePackage = async () => {
    if (!onSavePackage) return;
    
    setIsSaving(true);
    setSaveStatus(null);
    
    try {
      await onSavePackage();
      setSaveStatus('success');
    } catch (error) {
      console.error('Save failed:', error);
      setSaveStatus('error');
    } finally {
      setIsSaving(false);
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  const handleApprovePackage = async () => {
    if (!onApprovePackage) {
      setApproved(!approved);
      return;
    }
    
    try {
      await onApprovePackage();
      setApproved(true);
    } catch (error) {
      console.error('Approval failed:', error);
    }
  };

  // MAIN FEATURE: Chat revision connected to your API
  const handleChatSubmit = async () => {
    if (!chatMessage.trim() || !onRevisionRequest) return;
    
    const userMessage: ChatMessage = {
      id: Date.now(),
      type: 'user',
      message: chatMessage.trim(),
      timestamp: 'Just now',
      priority: selectedPriority
    };
    
    setChatHistory(prev => [...prev, userMessage]);
    
    // Clear input immediately for better UX
    const messageToSubmit = chatMessage.trim();
    setChatMessage('');
    
    try {
      // Call your actual revision API endpoint
      await onRevisionRequest(messageToSubmit, selectedPriority);
      
      // Add confirmation message
      const confirmationMessage: ChatMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        message: `Revision request submitted with ${selectedPriority} priority. The visual demo will be updated based on your feedback. You can track the progress in the package status.`,
        timestamp: 'Just now'
      };
      
      setChatHistory(prev => [...prev, confirmationMessage]);
      
    } catch (error) {
      console.error('Revision request failed:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: Date.now() + 1,
        type: 'assistant', 
        message: 'Sorry, the revision request failed. Please try again or use the traditional revision dialog.',
        timestamp: 'Just now'
      };
      
      setChatHistory(prev => [...prev, errorMessage]);
    }
  };

  const getSaveStatusIcon = () => {
    switch (saveStatus) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Save className="h-4 w-4" />;
    }
  };

  const getSaveStatusText = () => {
    switch (saveStatus) {
      case 'success':
        return 'Saved';
      case 'error':
        return 'Error';
      default:
        return 'Save Package';
    }
  };

  const getPackageStatusBadge = () => {
    const statusConfig = {
      draft: { color: 'bg-gray-100 text-gray-800', label: 'Draft' },
      generated: { color: 'bg-blue-100 text-blue-800', label: 'Generated' },
      under_review: { color: 'bg-yellow-100 text-yellow-800', label: 'Under Review' },
      needs_revision: { color: 'bg-orange-100 text-orange-800', label: 'Needs Revision' },
      approved: { color: 'bg-green-100 text-green-800', label: 'Approved' },
      rejected: { color: 'bg-red-100 text-red-800', label: 'Rejected' },
      published: { color: 'bg-purple-100 text-purple-800', label: 'Published' }
    };
    
    const config = statusConfig[packageStatus] || statusConfig.generated;
    
    return (
      <Badge className={`${config.color} text-xs`}>
        {config.label}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      <Card className="h-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5" />
              Interactive Visual Demo
              <Badge variant="secondary" className="ml-2">p5.js</Badge>
              {getPackageStatusBadge()}
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={runDemo} disabled={isRunning}>
                {isRunning ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Preview
                  </>
                )}
              </Button>
              <Button variant="outline" size="sm" onClick={openInNewWindow}>
                <ExternalLink className="mr-2 h-4 w-4" />
                Open Demo
              </Button>
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Maximize2 className="mr-2 h-4 w-4" />
                    Fullscreen
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-6xl h-[80vh]">
                  <DialogHeader>
                    <DialogTitle>Fullscreen Demo Preview</DialogTitle>
                  </DialogHeader>
                  <div className="flex-1 bg-gray-900 rounded-lg p-4">
                    <div className="h-full flex items-center justify-center text-white">
                      <div className="text-center space-y-4">
                        <Eye className="h-16 w-16 mx-auto text-blue-400" />
                        <h3 className="text-xl font-semibold">{content.description}</h3>
                        <p className="text-gray-300">{content.user_instructions}</p>
                        <Button onClick={openInNewWindow} className="mt-4">
                          <ExternalLink className="mr-2 h-4 w-4" />
                          Launch Interactive Demo
                        </Button>
                      </div>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="preview">Preview</TabsTrigger>
              <TabsTrigger value="code">Code</TabsTrigger>
              <TabsTrigger value="chat" className="relative">
                Revise
                {isSubmittingRevision && (
                  <Loader2 className="h-3 w-3 ml-1 animate-spin" />
                )}
              </TabsTrigger>
              <TabsTrigger value="details">Details</TabsTrigger>
            </TabsList>

            <TabsContent value="preview" className="space-y-4">
              {/* Demo Description */}
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  Demo Description
                </h4>
                <p className="text-sm text-blue-800">
                  {content.description || 'No description available'}
                </p>
              </div>

              {/* User Instructions */}
              {content.user_instructions && (
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-medium text-green-900 mb-2 flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    How to Interact
                  </h4>
                  <p className="text-sm text-green-800">{content.user_instructions}</p>
                </div>
              )}

              {/* Demo Preview Area */}
              <div className="bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 rounded-lg p-6 min-h-[300px] flex items-center justify-center relative overflow-hidden">
                {/* Animated background effect */}
                <div className="absolute inset-0 opacity-20">
                  <div className="absolute top-10 left-10 w-20 h-20 bg-blue-400 rounded-full animate-pulse"></div>
                  <div className="absolute top-20 right-20 w-16 h-16 bg-purple-400 rounded-full animate-bounce"></div>
                  <div className="absolute bottom-20 left-20 w-12 h-12 bg-green-400 rounded-full animate-ping"></div>
                </div>
                
                {isRunning ? (
                  <div className="space-y-6 text-center relative z-10">
                    <div className="relative">
                      <div className="w-24 h-24 mx-auto bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl flex items-center justify-center animate-pulse">
                        <Play className="h-12 w-12 text-white" />
                      </div>
                      <div className="absolute inset-0 w-24 h-24 mx-auto border-4 border-blue-400 rounded-2xl animate-ping"></div>
                    </div>
                    <div className="text-white">
                      <p className="text-lg font-medium">Running Demonstration...</p>
                      <p className="text-sm text-gray-300 mt-1">Initializing p5.js visualization</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6 text-center relative z-10">
                    <div className="w-24 h-24 mx-auto bg-gradient-to-r from-gray-700 to-gray-600 rounded-2xl flex items-center justify-center">
                      <Eye className="h-12 w-12 text-gray-300" />
                    </div>
                    <div className="text-white">
                      <p className="text-lg font-medium">{content.description || 'Visual Demo'}</p>
                      <p className="text-sm text-gray-300 mt-1">Click "Preview" or "Open Demo" to run the visualization</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Interactive Elements and Concepts */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2 flex items-center gap-2">
                    <Settings className="h-4 w-4" />
                    Interactive Elements
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {content.interactive_elements?.map((element, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {element.replace('_', ' ')}
                      </Badge>
                    )) || <span className="text-sm text-gray-500">None specified</span>}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Concepts Demonstrated</h4>
                  <div className="flex flex-wrap gap-2">
                    {content.concepts_demonstrated?.map((concept, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {concept.replace('_', ' ')}
                      </Badge>
                    )) || <span className="text-sm text-gray-500">None specified</span>}
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="code" className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  p5.js Source Code
                </h4>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={copyCode}>
                    <Copy className="mr-2 h-4 w-4" />
                    Copy
                  </Button>
                  <Button variant="outline" size="sm" onClick={downloadCode}>
                    <Download className="mr-2 h-4 w-4" />
                    Download
                  </Button>
                </div>
              </div>
              
              <div className="bg-gray-900 rounded-lg overflow-hidden">
                <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
                  <span className="text-sm text-gray-300">visual-demo-{packageId}.js</span>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                </div>
                <ScrollArea className="h-96">
                  <pre className="p-4 text-sm text-green-400 whitespace-pre-wrap font-mono">
                    <code>{content.p5_code || '// No code available'}</code>
                  </pre>
                </ScrollArea>
              </div>
              
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                <div className="flex gap-2">
                  <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-yellow-800">
                    <p className="font-medium">Security Note:</p>
                    <p>Code runs in a sandboxed environment when opened in a new window.</p>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="chat" className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  <h4 className="font-medium">Chat to Revise Demo</h4>
                  <Badge variant="secondary">AI Revision</Badge>
                </div>
                
                {/* Priority Selector */}
                <div className="flex items-center gap-2">
                  <Label className="text-sm">Priority:</Label>
                  <select 
                    value={selectedPriority} 
                    onChange={(e) => setSelectedPriority(e.target.value as 'low' | 'medium' | 'high')}
                    className="text-sm border rounded px-2 py-1"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
              </div>
              
              <Card className="h-96 flex flex-col">
                <CardContent className="flex-1 p-0">
                  <ScrollArea className="h-full p-4">
                    <div className="space-y-4">
                      {chatHistory.length === 0 && (
                        <div className="text-center text-gray-500 py-8">
                          <Bot className="h-12 w-12 mx-auto mb-2 text-gray-400" />
                          <p className="text-sm">Start a conversation to request revisions to this visual demo.</p>
                          <p className="text-xs mt-1">Your requests will be sent directly to the revision API.</p>
                        </div>
                      )}
                      
                      {chatHistory.map((message) => (
                        <div
                          key={message.id}
                          className={`flex gap-3 ${
                            message.type === 'user' ? 'justify-end' : 'justify-start'
                          }`}
                        >
                          <div
                            className={`max-w-[80%] rounded-lg p-3 ${
                              message.type === 'user'
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-100 text-gray-900'
                            }`}
                          >
                            <div className="flex items-center gap-2 mb-1">
                              {message.type === 'user' ? (
                                <User className="h-4 w-4" />
                              ) : (
                                <Bot className="h-4 w-4" />
                              )}
                              <span className="text-xs opacity-70">
                                {message.timestamp}
                              </span>
                              {message.priority && message.type === 'user' && (
                                <Badge variant="outline" className="text-xs">
                                  {message.priority}
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm">{message.message}</p>
                          </div>
                        </div>
                      ))}
                      
                      {isSubmittingRevision && (
                        <div className="flex gap-3 justify-start">
                          <div className="bg-gray-100 text-gray-900 rounded-lg p-3">
                            <div className="flex items-center gap-2">
                              <Loader2 className="h-4 w-4 animate-spin" />
                              <span className="text-sm">Processing revision request...</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
                <Separator />
                <CardFooter className="p-4">
                  <div className="flex w-full gap-2">
                    <Textarea
                      placeholder="Describe what you'd like to change about the visual demo..."
                      value={chatMessage}
                      onChange={(e) => setChatMessage(e.target.value)}
                      rows={2}
                      className="flex-1"
                      disabled={isSubmittingRevision}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleChatSubmit();
                        }
                      }}
                    />
                    <Button 
                      onClick={handleChatSubmit} 
                      disabled={!chatMessage.trim() || isSubmittingRevision || !onRevisionRequest}
                      size="sm"
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                </CardFooter>
              </Card>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex gap-2">
                  <AlertCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium">Revision Process:</p>
                    <p className="text-xs mt-1">
                      Your feedback will be sent to the revision API endpoint for processing. 
                      The visual demo will be regenerated based on your specific requests.
                    </p>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="details" className="space-y-4">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Technical Specifications</h4>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Framework:</span>
                      <span className="font-medium">p5.js</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Package ID:</span>
                      <span className="font-medium font-mono text-xs">{packageId}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Subject:</span>
                      <span className="font-medium">{subject}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Unit:</span>
                      <span className="font-medium">{unit}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Code Lines:</span>
                      <span className="font-medium">{content.p5_code?.split('\n').length || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Interactive:</span>
                      <span className="font-medium">
                        {content.interactive_elements && content.interactive_elements.length > 0 ? 'Yes' : 'Static'}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <h4 className="font-medium">Content Analysis</h4>
                  <div className="space-y-3">
                    <div className="text-sm">
                      <span className="text-muted-foreground">Interactive Elements:</span>
                      <span className="ml-2 font-medium">{content.interactive_elements?.length || 0}</span>
                    </div>
                    <div className="text-sm">
                      <span className="text-muted-foreground">Concepts Covered:</span>
                      <span className="ml-2 font-medium">{content.concepts_demonstrated?.length || 0}</span>
                    </div>
                    <div className="text-sm">
                      <span className="text-muted-foreground">Has Instructions:</span>
                      <span className="ml-2 font-medium">{content.user_instructions ? 'Yes' : 'No'}</span>
                    </div>
                    <div className="text-sm">
                      <span className="text-muted-foreground">Status:</span>
                      <span className="ml-2">{getPackageStatusBadge()}</span>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>

        <CardFooter className="flex justify-between border-t bg-gray-50">
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <MessageSquare className="mr-2 h-4 w-4" />
              Add Note
            </Button>
            <Button variant="outline" size="sm">
              <RefreshCw className="mr-2 h-4 w-4" />
              Regenerate
            </Button>
          </div>
          
          <div className="flex gap-2">
            {onSavePackage && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleSavePackage}
                disabled={isSaving}
              >
                {isSaving ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  getSaveStatusIcon()
                )}
                {isSaving ? 'Saving...' : getSaveStatusText()}
              </Button>
            )}
            <Button 
              size="sm" 
              variant={approved ? "default" : "outline"}
              onClick={handleApprovePackage}
              disabled={isSubmittingRevision}
            >
              <Check className="mr-2 h-4 w-4" />
              {approved ? 'Approved' : 'Approve'}
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};

// Also export as default
export default VisualDemoPanel;