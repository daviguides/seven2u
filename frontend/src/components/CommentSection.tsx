import { MessageCircle, Send } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";

import { api } from "../api/client";
import type { Comment } from "../api/types";
import { cn, formatDate } from "../lib/utils";
import { Skeleton } from "./LoadingStates";
import { useToast } from "./Toast";

interface CommentSectionProps {
  seriesId: number;
  episodeId?: number;
  compact?: boolean;
}

const MAX_LENGTH = 2000;

export function CommentSection({
  seriesId,
  episodeId,
  compact = false,
}: CommentSectionProps) {
  const { notify } = useToast();
  const [comments, setComments] = useState<Comment[] | null>(null);
  const [draft, setDraft] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .listComments(seriesId, episodeId)
      .then((list) => {
        if (!cancelled) setComments(list);
      })
      .catch(() => {
        if (!cancelled) {
          setComments([]);
          notify("Could not load comments");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [seriesId, episodeId, notify]);

  const canSubmit = draft.trim().length > 0 && !submitting;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    try {
      const created = await api.addComment(seriesId, draft.trim(), episodeId);
      setComments((list) => [...(list ?? []), created]);
      setDraft("");
    } catch (err) {
      notify(err instanceof Error ? err.message : "Could not post comment");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section
      aria-label={episodeId ? "Episode comments" : "Series comments"}
      className={cn("card", compact ? "p-3" : "p-4 sm:p-5")}
    >
      <h3 className="mb-3 inline-flex items-center gap-2 text-sm font-semibold">
        <MessageCircle size={16} className="text-primary" />
        {episodeId ? "Episode notes" : "Your notes"}
        {comments && comments.length > 0 && (
          <span className="font-mono text-xs text-text-muted">
            {comments.length}
          </span>
        )}
      </h3>

      {comments === null ? (
        <div className="space-y-2">
          <Skeleton className="h-3 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      ) : comments.length === 0 ? (
        <p className="text-sm text-text-muted">
          No notes yet. Leave a thought for future you.
        </p>
      ) : (
        <ul className="space-y-2">
          {comments.map((c) => (
            <li
              key={c.id}
              className="rounded-btn bg-elevated px-3 py-2 text-sm"
            >
              <p className="whitespace-pre-wrap break-words">{c.content}</p>
              <time
                dateTime={c.created_at}
                className="mt-1 block font-mono text-[11px] text-text-muted"
              >
                {formatDate(c.created_at)}
              </time>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={submit} className="mt-3 flex items-end gap-2">
        <label className="flex-1">
          <span className="sr-only">New note</span>
          <textarea
            value={draft}
            maxLength={MAX_LENGTH}
            onChange={(e) => setDraft(e.target.value)}
            rows={compact ? 2 : 3}
            placeholder="Write a note…"
            className="focus-ring w-full resize-y rounded-btn border border-border bg-surface px-3 py-2 text-sm placeholder:text-text-muted"
          />
        </label>
        <button
          type="submit"
          disabled={!canSubmit}
          aria-label="Post note"
          className="focus-ring inline-flex h-9 items-center gap-1.5 rounded-btn bg-primary px-3 text-sm font-semibold text-bg transition hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Send size={14} />
          <span className="hidden sm:inline">Post</span>
        </button>
      </form>
    </section>
  );
}
