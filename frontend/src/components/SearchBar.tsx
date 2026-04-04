"use client";

import { useEffect, useRef, useState } from "react";
import { searchCards, type SearchResult, AuthError } from "@/lib/api";

type Props = {
  boardId: number;
  onAuthError?: () => void;
};

export function SearchBar({ boardId, onAuthError }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setOpen(false);
      return;
    }

    setLoading(true);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const r = await searchCards(boardId, query);
        setResults(r);
        setOpen(true);
      } catch (err) {
        if (err instanceof AuthError) onAuthError?.();
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(debounceRef.current);
  }, [query, boardId, onAuthError]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        placeholder="Search cards..."
        className="w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2.5 text-sm outline-none focus:border-[var(--primary-blue)]"
        aria-label="Search cards"
      />
      {loading && (
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[var(--gray-text)]">
          ...
        </span>
      )}

      {open && results.length > 0 && (
        <div className="absolute left-0 right-0 top-full z-50 mt-2 max-h-80 overflow-y-auto rounded-xl border border-[var(--stroke)] bg-white shadow-[0_12px_24px_rgba(3,33,71,0.12)]">
          {results.map((r) => (
            <div
              key={r.id}
              className="border-b border-[var(--stroke)] px-4 py-3 last:border-0"
            >
              <p className="text-sm font-semibold text-[var(--navy-dark)]">
                {r.title}
              </p>
              {r.details && (
                <p className="mt-0.5 text-xs text-[var(--gray-text)] line-clamp-1">
                  {r.details}
                </p>
              )}
              <p className="mt-1 text-[10px] font-semibold uppercase tracking-wider text-[var(--primary-blue)]">
                {r.column_title}
              </p>
            </div>
          ))}
        </div>
      )}

      {open && query.trim() && results.length === 0 && !loading && (
        <div className="absolute left-0 right-0 top-full z-50 mt-2 rounded-xl border border-[var(--stroke)] bg-white px-4 py-3 shadow-[0_12px_24px_rgba(3,33,71,0.12)]">
          <p className="text-sm text-[var(--gray-text)]">No cards found</p>
        </div>
      )}
    </div>
  );
}
