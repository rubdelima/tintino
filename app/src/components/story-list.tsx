"use client";

import React, { useEffect, useState } from 'react';
import type { Story } from '@/lib/types';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Paintbrush } from 'lucide-react';
import { useAuth } from '@/hooks/use-auth.tsx';
import { Skeleton } from './ui/skeleton';
import { getApiEndpoint } from '@/lib/api-config';

interface StoryListProps {
  onSelectStory: (story: Story) => void;
  selectedStoryId?: string | null;
}

const isEmoji = (str: string | null | undefined) => {
  if (!str) return false;
  const emojiRegex = /(\u00a9|\u00ae|[\u2000-\u3300]|\ud83c[\ud000-\udfff]|\ud83d[\ud000-\udfff]|\ud83e[\ud000-\udfff])/g;
  return emojiRegex.test(str) && str.match(emojiRegex)?.length === 1;
};

export function StoryList({ onSelectStory, selectedStoryId }: StoryListProps) {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);
  const { firebaseToken } = useAuth();

  useEffect(() => {
    const fetchStories = async () => {
      if (!firebaseToken) {
        setLoading(false);
        return;
      };

      setLoading(true);
      try {
        const response = await fetch(getApiEndpoint('CHATS'), {
          headers: {
            'Authorization': `Bearer ${firebaseToken}`
          }
        });
        if (!response.ok) {
          throw new Error('Failed to fetch stories');
        }
        const data = await response.json();
        setStories(data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    fetchStories();
  }, [firebaseToken]);


  const renderStory = (story: Story) => (
    <button
      key={story.chat_id}
      onClick={() => onSelectStory(story)}
      className={`w-full text-left p-3 rounded-lg transition-colors text-sm flex items-center gap-3 ${
        selectedStoryId === story.chat_id ? 'bg-sidebar-accent font-semibold' : 'hover:bg-sidebar-accent/50'
      }`}
    >
      <div className="p-2 text-xl rounded-md">
        {isEmoji(story.chat_image) ? story.chat_image : '🎨'}
      </div>
      <span>{story.title}</span>
    </button>
  );

  if (loading) {
    return (
        <div className="p-4 space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
        </div>
    )
  }

  return (
    <ScrollArea className="flex-1">
      <div className="p-4 space-y-6">
        <div>
          <h3 className="px-3 mb-2 text-xs font-bold tracking-wider text-muted-foreground uppercase">Your Stories</h3>
          <div className="space-y-1">
            {stories.length > 0 ? (
                stories.map(renderStory)
            ) : (
                <p className="px-3 text-sm text-muted-foreground">You don't have any stories yet. Create one!</p>
            )}
          </div>
        </div>
      </div>
    </ScrollArea>
  );
}
