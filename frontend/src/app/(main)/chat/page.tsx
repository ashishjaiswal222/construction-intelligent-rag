'use client';

import * as React from 'react';
import { useAppStore } from '@/store';
import { useChatStore } from '@/store/chat';
import { ChatMessage, ChatMessageData } from '@/components/chat/ChatMessage';
import { generateAnswer } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Square, FolderOpen, Bot, MessageSquare, Trash2, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';

const SUGGESTIONS = [
  "What is the rate for item 2.6.1 in the BOQ?",
  "What does clause 5 say about liquidated damages?",
  "Summarize the recent structural drawing revisions.",
];

import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger, DropdownMenuGroup } from '@/components/ui/dropdown-menu';
import { ChevronDown } from 'lucide-react';

export default function ChatPage() {
  const { activeProject } = useAppStore();
  
  // Chat store state
  const { 
    sessions, 
    activeSessionId, 
    setActiveSession, 
    createSession, 
    deleteSession, 
    updateSessionMessages, 
    updateSessionTitle,
    getSessionsForProject
  } = useChatStore();

  const [input, setInput] = React.useState('');
  const [isStreaming, setIsStreaming] = React.useState(false);
  const scrollRef = React.useRef<HTMLDivElement>(null);
  const eventSourceRef = React.useRef<EventSource | null>(null);

  const activeSession = sessions.find(s => s.id === activeSessionId);
  const messages = activeSession?.messages || [];
  const projectSessions = activeProject ? getSessionsForProject(activeProject.project_id) : [];

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Ensure an active session exists if we switch projects, or clear it if the session belongs to another project
  React.useEffect(() => {
    if (activeProject && activeSessionId) {
      const session = sessions.find(s => s.id === activeSessionId);
      if (session && session.projectId !== activeProject.project_id) {
        setActiveSession(null);
      }
    }
  }, [activeProject, activeSessionId, sessions, setActiveSession]);

  const handleNewChat = () => {
    if (activeProject) {
      createSession(activeProject.project_id);
    }
  };

  const abortStream = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
    
    if (activeSessionId) {
      const msgs = [...messages];
      if (msgs.length > 0 && msgs[msgs.length - 1].role === 'assistant' && msgs[msgs.length - 1].status !== 'done') {
        msgs[msgs.length - 1].status = 'error';
        msgs[msgs.length - 1].errorMessage = 'Stream aborted by user.';
        updateSessionMessages(activeSessionId, msgs);
      }
    }
  };

  const handleSend = async (text: string) => {
    if (!text.trim() || !activeProject) return;

    let sessionId = activeSessionId;
    let isFirstMessage = false;

    // Auto-create session if none active
    if (!sessionId) {
      sessionId = createSession(activeProject.project_id);
      isFirstMessage = true;
    } else if (messages.length === 0) {
      isFirstMessage = true;
    }

    if (isFirstMessage) {
      // Auto title based on first message
      const shortTitle = text.slice(0, 30) + (text.length > 30 ? '...' : '');
      updateSessionTitle(sessionId, shortTitle);
    }

    const userMessageId = Date.now().toString();
    const assistantMessageId = (Date.now() + 1).toString();

    // Use current messages if session already existed, otherwise empty array
    const currentMessages = isFirstMessage ? [] : messages;
    
    const newMessages: ChatMessageData[] = [
      ...currentMessages,
      { id: userMessageId, role: 'user', content: text },
      { id: assistantMessageId, role: 'assistant', content: '', status: 'generating' }
    ];
    
    updateSessionMessages(sessionId, newMessages);
    setInput('');
    setIsStreaming(true);

    try {
      const chatHistory = currentMessages.slice(-8).map(m => ({
        role: m.role,
        content: m.content
      }));
      
      const response = await generateAnswer(activeProject.project_id, text, chatHistory);
      
      // Update the specific session's messages
      const session = useChatStore.getState().sessions.find(s => s.id === sessionId);
      if (session) {
        const arr = [...session.messages];
        const last = arr[arr.length - 1];
        if (last.id === assistantMessageId) {
          arr[arr.length - 1] = {
            ...last,
            status: 'done',
            log_id: response.log_id,
            content: response.answer,
            citations: response.citations,
            confidence: response.confidence,
            answer_grounded: response.answer_grounded,
            needs_fallback: response.needs_fallback,
            warning_message: response.warning_message || undefined
          };
          updateSessionMessages(sessionId, arr);
        }
      }
    } catch (err) {
      console.error(err);
      const session = useChatStore.getState().sessions.find(s => s.id === sessionId);
      if (session) {
        const msgs = [...session.messages];
        msgs[msgs.length - 1].status = 'error';
        msgs[msgs.length - 1].errorMessage = 'Network error while generating answer.';
        updateSessionMessages(sessionId, msgs);
      }
    } finally {
      setIsStreaming(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full p-8 text-center bg-card rounded-lg border">
        <FolderOpen className="w-16 h-16 text-muted-foreground mb-4" />
        <h2 className="text-xl font-bold mb-2">No Project Selected</h2>
        <p className="text-muted-foreground max-w-md">
          Please select an active project from the top bar to start chatting with its documents.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-background rounded-xl border overflow-hidden relative">
      <div className="flex items-center justify-between p-4 border-b bg-muted/20">
        <div className="flex items-center gap-2">
          <DropdownMenu>
            <DropdownMenuTrigger className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-9 px-4 py-2 gap-2">
              <Bot className="w-4 h-4" />
              <span className="max-w-[200px] truncate">{activeSession ? activeSession.title : 'New Chat Session'}</span>
              <ChevronDown className="w-4 h-4 ml-2 opacity-50" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-64 max-h-[400px] overflow-y-auto">
              <DropdownMenuGroup>
                <DropdownMenuLabel>Recent Chats</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {projectSessions.length === 0 ? (
                  <div className="text-sm text-muted-foreground p-2 text-center">No recent chats</div>
                ) : (
                  projectSessions.map(session => (
                    <div key={session.id} className="flex items-center group">
                      <DropdownMenuItem 
                        className="flex-1 cursor-pointer truncate"
                        onClick={() => setActiveSession(session.id)}
                      >
                        <MessageSquare className="w-4 h-4 mr-2 shrink-0 opacity-50" />
                        <span className="truncate">{session.title}</span>
                      </DropdownMenuItem>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteSession(session.id);
                        }}
                        className="p-2 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Delete chat"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))
                )}
              </DropdownMenuGroup>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <Button onClick={handleNewChat} variant="outline" size="sm" className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Chat
        </Button>
      </div>
      
      <div className="flex-1 overflow-y-auto min-h-0 p-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-24">
            <div className="w-16 h-16 bg-primary/10 text-primary rounded-2xl flex items-center justify-center mb-6">
              <Bot className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Constelligence Assistant</h2>
            <p className="text-muted-foreground max-w-md mb-8">
              Ask questions about contracts, BOQs, drawings, and specifications for the {activeProject.name} project.
            </p>
            <div className="grid gap-3 w-full max-w-lg">
              {SUGGESTIONS.map((s, i) => (
                <Button 
                  key={i} 
                  variant="outline" 
                  className="justify-start text-left h-auto py-3 whitespace-normal"
                  onClick={() => handleSend(s)}
                >
                  {s}
                </Button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-6 pb-24 max-w-5xl mx-auto">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            <div ref={scrollRef} />
          </div>
        )}
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-4 bg-background/80 backdrop-blur-sm border-t">
        <div className="max-w-4xl mx-auto relative flex items-end gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about the project documents..."
            className="min-h-[60px] max-h-[200px] resize-none pr-24 pb-8"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend(input);
              }
            }}
            maxLength={2000}
            disabled={isStreaming}
          />
          
          <div className="absolute right-16 bottom-3 text-xs text-muted-foreground font-mono">
            {input.length}/2000
          </div>

          {isStreaming ? (
            <Button 
              onClick={abortStream} 
              variant="destructive" 
              size="icon" 
              className="h-[60px] w-[60px] shrink-0"
              title="Stop generating"
            >
              <Square className="h-5 w-5 fill-current" />
            </Button>
          ) : (
            <Button 
              onClick={() => handleSend(input)} 
              disabled={!input.trim() || isStreaming}
              size="icon"
              className="h-[60px] w-[60px] shrink-0"
            >
              <Send className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
