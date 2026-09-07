'use client';

import * as React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { SourceCitation } from './SourceCitation';
import { Bot, User, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { DocType, Citation } from '@/types';

export type MessageRole = 'user' | 'assistant';

export interface ChatMessageData {
  id: string;
  role: MessageRole;
  content: string;
  status?: 'generating' | 'done' | 'error' | 'no_context';
  log_id?: string;
  citations?: Citation[];
  confidence?: number;
  answer_grounded?: boolean;
  needs_fallback?: boolean;
  warning_message?: string;
  errorMessage?: string;
}

interface Props {
  message: ChatMessageData;
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user';

  return (
    <div className={cn("flex gap-4 py-4 w-full", isUser ? "flex-row-reverse" : "flex-row")}>
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
        isUser ? "bg-primary text-primary-foreground" : "bg-muted text-foreground border"
      )}>
        {isUser ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
      </div>
      
      <div className={cn(
        "flex flex-col gap-2 max-w-[80%]",
        isUser ? "items-end" : "items-start"
      )}>
        <div className={cn(
          "px-4 py-3 rounded-xl",
          isUser 
            ? "bg-primary text-primary-foreground rounded-tr-sm" 
            : "bg-card border rounded-tl-sm shadow-sm"
        )}>
          {isUser ? (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
              
              {!message.content && message.status === 'generating' && (
                <div className="flex items-center gap-2 text-muted-foreground text-sm py-1">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Retrieving documents and generating answer...</span>
                </div>
              )}
            </div>
          )}
        </div>

        {message.status === 'no_context' && (
          <div className="flex items-center gap-2 text-amber-500 text-sm mt-1">
            <AlertCircle className="w-4 h-4" />
            <span>No relevant context found in documents. Try rephrasing your query.</span>
          </div>
        )}

        {message.status === 'error' && (
          <div className="flex items-center gap-2 text-red-500 text-sm mt-1">
            <AlertCircle className="w-4 h-4" />
            <span>{message.errorMessage || 'An error occurred while fetching the response.'}</span>
          </div>
        )}

        {/* Phase 8 Hallucination & Fallback Warnings */}
        {message.needs_fallback && (
          <div className="flex items-center gap-2 text-amber-600 bg-amber-50 dark:bg-amber-950/30 p-2 rounded-md border border-amber-200 dark:border-amber-900 w-full mt-1">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="text-xs">Exact match not found. Showing closest available documents.</span>
          </div>
        )}

        {message.answer_grounded === false && message.warning_message && (
          <div className="flex items-start gap-2 text-red-600 bg-red-50 dark:bg-red-950/30 p-2 rounded-md border border-red-200 dark:border-red-900 w-full mt-1">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span className="text-xs font-medium">{message.warning_message}</span>
          </div>
        )}

        {message.citations && message.citations.length > 0 && (
          <div className="w-full mt-2">
            <div className="flex justify-between items-center mb-2">
              <div className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Sources Used ({message.citations.length})
              </div>
              {message.confidence !== undefined && (
                <div className="text-[10px] bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
                  Conf: {(message.confidence * 100).toFixed(1)}%
                </div>
              )}
            </div>
            <div className="grid gap-2 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 w-full">
              {message.citations.map((c, i) => (
                <SourceCitation key={i} source={c} index={i + 1} />
              ))}
            </div>
          </div>
        )}

        {!isUser && message.log_id && message.status === 'done' && (
          <div className="flex items-center gap-2 mt-2 pt-2 border-t w-full opacity-60 hover:opacity-100 transition-opacity">
            <span className="text-[10px] text-muted-foreground mr-1">Was this helpful?</span>
            <button 
              onClick={() => {
                import('@/lib/api/generation').then(m => m.sendFeedback(message.log_id!, true));
              }}
              className="text-muted-foreground hover:text-emerald-500 transition-colors"
              title="Helpful"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg>
            </button>
            <button 
              onClick={() => {
                import('@/lib/api/generation').then(m => m.sendFeedback(message.log_id!, false));
              }}
              className="text-muted-foreground hover:text-red-500 transition-colors"
              title="Not helpful"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path></svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
