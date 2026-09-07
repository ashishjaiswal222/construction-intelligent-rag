'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getProjects } from '@/lib/api';
import { useAppStore } from '@/store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { MapPin, Building2, Calendar } from 'lucide-react';
import { CreateProjectModal } from './CreateProjectModal';

export function ProjectsList() {
  const { activeProject, setActiveProject } = useAppStore();
  const { data, isLoading, isError } = useQuery({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  const projects = data?.projects || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Projects</h2>
          <p className="text-muted-foreground">Manage your construction projects.</p>
        </div>
        <CreateProjectModal />
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-40 w-full rounded-xl" />
          ))}
        </div>
      ) : isError ? (
        <div className="p-4 border border-red-200 bg-red-50 text-red-700 rounded-md">
          Failed to load projects. Please try again later.
        </div>
      ) : projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center border rounded-lg bg-background/50 border-dashed">
          <Building2 className="w-12 h-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold">No projects found</h3>
          <p className="text-muted-foreground max-w-sm mb-4">
            Get started by creating your first construction project to manage documents and chat.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Card 
              key={project.project_id} 
              className={`cursor-pointer transition-colors hover:border-primary ${
                activeProject?.project_id === project.project_id ? 'border-primary shadow-sm bg-primary/5' : ''
              }`}
              onClick={() => setActiveProject(project)}
            >
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-lg">{project.name}</CardTitle>
                  {activeProject?.project_id === project.project_id && (
                    <Badge variant="default">Active</Badge>
                  )}
                </div>
                <CardDescription className="flex items-center gap-1 mt-1">
                  <MapPin className="w-3 h-3" />
                  {project.location}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Building2 className="w-4 h-4" />
                    {project.type}
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    Phase: <span className="font-medium text-foreground">{project.phase}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
