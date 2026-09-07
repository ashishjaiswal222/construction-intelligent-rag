'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getHealth, getProjects } from '@/lib/api';
import { useAppStore } from '@/store';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';

export function Topbar() {
  const { activeProject, setActiveProject } = useAppStore();

  const { data: projectsData } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 30000, // Poll every 30s
  });

  const projects = projectsData?.projects || [];

  // Auto-select first project if none is active, or if active project is invalid
  React.useEffect(() => {
    if (!projectsData) return; // wait for fetch to complete
    
    if (projects.length > 0) {
      if (!activeProject || !projects.find(p => p.project_id === activeProject.project_id)) {
        setActiveProject(projects[0]);
      }
    } else if (activeProject) {
      setActiveProject(null);
    }
  }, [projectsData, projects, activeProject, setActiveProject]);

  const healthColor = React.useMemo(() => {
    if (!healthData) return 'bg-gray-400';
    if (healthData.status === 'ok') return 'bg-emerald-500';
    return 'bg-amber-500'; // degraded
  }, [healthData]);

  return (
    <header className="h-14 border-b flex items-center justify-between px-6 bg-background">
      <div className="flex items-center gap-4">
        <DropdownMenu>
          <DropdownMenuTrigger render={<Button variant="outline" className="w-[240px] justify-between" />}>
            <span className="truncate">
              {activeProject ? activeProject.name : 'Select a Project'}
            </span>
            <ChevronDown className="h-4 w-4 opacity-50" />
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-[240px]">
            <DropdownMenuGroup>
              <DropdownMenuLabel>Your Projects</DropdownMenuLabel>
            </DropdownMenuGroup>
            <DropdownMenuSeparator />
            {projects.map((p) => (
              <DropdownMenuItem 
                key={p.project_id}
                onClick={() => setActiveProject(p)}
                className="cursor-pointer"
              >
                {p.name}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        {activeProject && (
          <Badge variant="secondary" className="font-mono text-xs">
            {activeProject.phase} Phase
          </Badge>
        )}
      </div>

      <div className="flex items-center gap-6">
        <div className="relative w-64">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            type="search" 
            placeholder="Global search..." 
            className="w-full pl-8 h-9"
          />
        </div>

        <div className="flex items-center gap-2" title={healthData?.status || 'Unknown Status'}>
          <div className={`h-2.5 w-2.5 rounded-full ${healthColor} animate-pulse`} />
          <span className="text-xs text-muted-foreground hidden sm:inline-block">
            {healthData?.status === 'ok' ? 'System Normal' : healthData?.status === 'degraded' ? 'Degraded' : 'Checking...'}
          </span>
        </div>
      </div>
    </header>
  );
}
