'use client';

import { useState, useEffect } from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react';
import { voteCVE, getCVEVoteStatus, type CVEVoteResponse } from '@/lib/api';

interface CVEVoteButtonProps {
  cveId: string;
  initialUpvotes?: number;
  initialDownvotes?: number;
  compact?: boolean;
}

export function CVEVoteButton({
  cveId,
  initialUpvotes = 0,
  initialDownvotes = 0,
  compact = false
}: CVEVoteButtonProps) {
  const [voteData, setVoteData] = useState<CVEVoteResponse>({
    cve_id: cveId,
    upvotes: initialUpvotes,
    downvotes: initialDownvotes,
    user_vote: null,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [token, setToken] = useState<string | null>(null);

  // Check token on mount and when it changes
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    setToken(storedToken);

    // If no token, clear user_vote immediately
    if (!storedToken) {
      setVoteData(prev => ({
        ...prev,
        user_vote: null,
      }));
    }
  }, []); // Run only on mount

  // Watch for logout events
  useEffect(() => {
    const handleLogout = () => {
      setToken(null);
      // Clear user_vote when logged out
      setVoteData(prev => ({
        ...prev,
        user_vote: null,
      }));
    };

    window.addEventListener('auth-logout', handleLogout);
    return () => window.removeEventListener('auth-logout', handleLogout);
  }, []);

  // Load vote status when logged in
  useEffect(() => {
    if (!token) {
      return;
    }

    // Load cached vote status from localStorage
    const cacheKey = `vote_${cveId}`;
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      try {
        const cachedData = JSON.parse(cached);
        setVoteData(prev => ({
          ...prev,
          user_vote: cachedData.user_vote,
        }));
      } catch (e) {
        // Ignore invalid cache
      }
    }

    // Load vote status with delay to avoid rate limiting
    // Only if not already cached
    if (!cached) {
      const delay = Math.random() * 2000; // Random delay 0-2s
      const timer = setTimeout(() => {
        getCVEVoteStatus(cveId, token)
          .then(data => {
            setVoteData(prev => ({
              ...prev,
              user_vote: data.user_vote,
            }));
            // Cache the vote status
            localStorage.setItem(cacheKey, JSON.stringify({ user_vote: data.user_vote }));
          })
          .catch(() => {
            // Silently fail
          });
      }, delay);

      return () => clearTimeout(timer);
    }
  }, [cveId, token]);

  // Update vote data when props change
  useEffect(() => {
    setVoteData(prev => ({
      ...prev,
      upvotes: initialUpvotes,
      downvotes: initialDownvotes,
    }));
  }, [initialUpvotes, initialDownvotes]);

  const handleVote = async (voteType: 1 | -1) => {
    if (!token) {
      // Redirect to auth
      window.location.href = '/auth';
      return;
    }

    setIsLoading(true);
    try {
      const result = await voteCVE(cveId, voteType, token);
      setVoteData(result);

      // Update cache
      const cacheKey = `vote_${cveId}`;
      localStorage.setItem(cacheKey, JSON.stringify({ user_vote: result.user_vote }));
    } catch (error) {
      console.error('Failed to vote:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const netScore = voteData.upvotes - voteData.downvotes;
  const isUpvoted = voteData.user_vote === 1;
  const isDownvoted = voteData.user_vote === -1;

  if (compact) {
    return (
      <div className="flex flex-col items-center gap-1 min-w-[60px]">
        <button
          onClick={() => handleVote(1)}
          disabled={isLoading}
          className={`p-2 rounded-lg transition-all ${
            isUpvoted
              ? 'text-green-600 bg-green-100 dark:bg-green-900/30 shadow-sm'
              : 'text-gray-600 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20'
          } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          title="Upvote"
        >
          <ArrowUp className="h-5 w-5" />
        </button>

        <div className={`text-lg font-bold px-2 py-1 rounded ${
          netScore > 0
            ? 'text-green-600 bg-green-50 dark:bg-green-900/20'
            : netScore < 0
            ? 'text-red-600 bg-red-50 dark:bg-red-900/20'
            : 'text-gray-600 bg-gray-50'
        }`}>
          {netScore > 0 ? '+' : ''}{netScore}
        </div>

        <button
          onClick={() => handleVote(-1)}
          disabled={isLoading}
          className={`p-2 rounded-lg transition-all ${
            isDownvoted
              ? 'text-red-600 bg-red-100 dark:bg-red-900/30 shadow-sm'
              : 'text-gray-600 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20'
          } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          title="Downvote"
        >
          <ArrowDown className="h-5 w-5" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        onClick={() => handleVote(1)}
        disabled={isLoading}
        className={`p-2 rounded-lg transition-all ${
          isUpvoted
            ? 'text-green-600 bg-green-50 dark:bg-green-900/20 shadow-sm'
            : 'text-gray-500 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20'
        } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
        title="Upvote this CVE"
      >
        <ArrowUp className="h-5 w-5" />
      </button>

      <div className="flex flex-col items-center">
        <span className={`text-lg font-bold ${
          netScore > 0 ? 'text-green-600' : netScore < 0 ? 'text-red-600' : 'text-gray-600'
        }`}>
          {netScore > 0 ? '+' : ''}{netScore}
        </span>
        <span className="text-xs text-gray-500">
          {voteData.upvotes} ↑ {voteData.downvotes} ↓
        </span>
      </div>

      <button
        onClick={() => handleVote(-1)}
        disabled={isLoading}
        className={`p-2 rounded-lg transition-all ${
          isDownvoted
            ? 'text-red-600 bg-red-50 dark:bg-red-900/20 shadow-sm'
            : 'text-gray-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20'
        } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
        title="Downvote this CVE"
      >
        <ArrowDown className="h-5 w-5" />
      </button>
    </div>
  );
}
