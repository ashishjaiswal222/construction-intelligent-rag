import * as React from 'react';
import { Badge } from '@/components/ui/badge';
import { DocumentStatus } from '@/types';

interface Props {
  status: DocumentStatus | string;
  className?: string;
}

export function StatusBadge({ status, className }: Props) {
  let label = status.replace(/_/g, ' ');
  let variant: 'default' | 'destructive' | 'secondary' | 'outline' = 'outline';
  let customColor = '';

  switch (status) {
    case 'indexed':
      label = 'Indexed';
      variant = 'default';
      break;
    case 'failed':
      label = 'Failed';
      variant = 'destructive';
      break;
    case 'permanently_failed':
      label = 'Permanently Failed';
      variant = 'destructive';
      customColor = 'bg-red-800 hover:bg-red-900';
      break;
    case 'needs_review':
      label = 'Needs Review';
      variant = 'secondary';
      customColor = 'bg-amber-500 hover:bg-amber-600 text-white';
      break;
    case 'partially_indexed':
      label = 'Partially Indexed';
      variant = 'secondary';
      customColor = 'bg-amber-500 hover:bg-amber-600 text-white';
      break;
    case 'partial':
      label = 'Partially Complete';
      variant = 'secondary';
      customColor = 'bg-amber-500 hover:bg-amber-600 text-white';
      break;
    case 'splitting':
      label = 'Splitting Pages';
      variant = 'default';
      customColor = 'bg-blue-500 hover:bg-blue-600';
      break;
    case 'processing':
      label = 'Extracting Text';
      variant = 'default';
      customColor = 'bg-blue-500 hover:bg-blue-600';
      break;
    case 'aggregating':
      label = 'Aggregating Results';
      variant = 'default';
      customColor = 'bg-blue-500 hover:bg-blue-600';
      break;
    case 'refinement_processing':
      label = 'Refining Text';
      variant = 'default';
      customColor = 'bg-violet-500 hover:bg-violet-600';
      break;
    case 'queued':
      label = 'Queued';
      variant = 'secondary';
      break;
    case 'classifying':
    case 'classified':
    case 'ocr_processing':
    case 'chunking':
    case 'embedding_index':
      label = status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' ');
      variant = 'secondary';
      break;
    default:
      label = status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' ');
      variant = 'outline';
      break;
  }

  return (
    <Badge 
      variant={variant} 
      className={`${customColor} capitalize whitespace-nowrap ${className || ''}`}
    >
      {label}
    </Badge>
  );
}
