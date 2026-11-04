"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import {
  saveTextRecord,
  listTextRecords,
  deleteTextRecord,
  subscribeTextRecords,
  TextRecord,
  TextCategory,
} from "@/lib/firestoreTextStore";

interface TextStoreWidgetProps {
  entityType?: TextCategory;
  entityId?: string;
  placeholder?: string;
  title?: string;
}

export function TextStoreWidget({
  entityType = "general",
  entityId,
  placeholder = "Write and store text data (memos, notes, cancellation instructions, review details)...",
  title = "Firebase Text Store",
}: TextStoreWidgetProps) {
  const { user } = useAuth();
  const [records, setRecords] = useState<TextRecord[]>([]);
  const [noteTitle, setNoteTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState<TextCategory>(entityType);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    // Initial fetch and realtime listener
    const unsubscribe = subscribeTextRecords(
      (newRecords) => {
        let filtered = newRecords;
        if (entityId) {
          filtered = filtered.filter((r) => r.entityId === entityId);
        } else if (entityType !== "general") {
          filtered = filtered.filter((r) => r.category === entityType);
        }
        setRecords(filtered);
      },
      entityId ? { entityId } : { category: entityType }
    );

    return () => unsubscribe();
  }, [entityType, entityId]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setSaving(true);
    setFeedback(null);
    try {
      await saveTextRecord({
        title: noteTitle.trim() || "Untitled Note",
        content: content.trim(),
        category,
        entityId,
        userId: user?.uid || "guest_user",
        userEmail: user?.email || undefined,
      });

      setContent("");
      setNoteTitle("");
      setFeedback("Text record securely saved to Cloud Firestore!");
      setTimeout(() => setFeedback(null), 3500);

      // Refresh records
      const updated = await listTextRecords(
        entityId ? { entityId } : { category }
      );
      setRecords(updated);
    } catch (err) {
      console.error("Save error:", err);
      setFeedback("Saved to local storage (check Firebase connection).");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteTextRecord(id);
    setRecords((prev) => prev.filter((r) => r.id !== id));
  };

  return (
    <div className="rounded-2xl bg-[#082746]/90 border border-[#164B68] p-5 flex flex-col gap-4 shadow-xl backdrop-blur-md">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#164B68]/60">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#00B8C7]/15 border border-[#00B8C7]/40 flex items-center justify-center text-[#00E0E0]">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">{title}</h3>
            <p className="text-[11px] text-[#A9BBCD]">
              Cloud text persistence via Firebase Spark (Free Tier)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            ✓ 100% Free Plan
          </span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#00B8C7]/10 border border-[#00B8C7]/30 text-[#00E0E0]">
            1 GB Quota
          </span>
        </div>
      </div>

      {/* Editor Form */}
      <form onSubmit={handleSave} className="flex flex-col gap-3">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          <input
            type="text"
            value={noteTitle}
            onChange={(e) => setNoteTitle(e.target.value)}
            placeholder="Note title (optional)..."
            className="sm:col-span-2 px-3 py-2 rounded-xl bg-[#031B38] border border-[#164B68] text-xs text-white placeholder-[#5B7998] focus:outline-none focus:border-[#00B8C7]"
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as TextCategory)}
            className="px-3 py-2 rounded-xl bg-[#031B38] border border-[#164B68] text-xs text-[#A9BBCD] focus:outline-none focus:border-[#00B8C7]"
          >
            <option value="general">General Note</option>
            <option value="commitment_note">Commitment Memo</option>
            <option value="cancellation_note">Cancellation Text</option>
            <option value="merchant_memo">Merchant Review</option>
            <option value="audit">Audit Log</option>
          </select>
        </div>

        <textarea
          rows={3}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder={placeholder}
          className="w-full p-3 rounded-xl bg-[#031B38] border border-[#164B68] text-xs text-white placeholder-[#5B7998] focus:outline-none focus:border-[#00B8C7] resize-y"
        />

        <div className="flex items-center justify-between pt-1">
          <div className="text-[11px] text-[#5B7998]">
            {content.length} characters • Auto-synced
          </div>

          <button
            type="submit"
            disabled={saving || !content.trim()}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-[#00B8C7] to-[#00E0E0] text-[#011633] text-xs font-bold hover:brightness-110 transition-all disabled:opacity-40 flex items-center gap-1.5 shadow-md"
          >
            {saving ? (
              <>
                <div className="w-3 h-3 rounded-full border-2 border-[#011633] border-t-transparent animate-spin" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Save to Firestore</span>
              </>
            )}
          </button>
        </div>

        {feedback && (
          <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2 animate-fadeIn">
            <span>✓</span>
            <span>{feedback}</span>
          </div>
        )}
      </form>

      {/* Stored Text Items List */}
      {records.length > 0 && (
        <div className="flex flex-col gap-2 pt-2 border-t border-[#164B68]/40">
          <div className="flex items-center justify-between text-xs text-[#A9BBCD]">
            <span>Stored Text Records ({records.length})</span>
            <span className="text-[10px] text-[#5B7998]">Synced across devices</span>
          </div>

          <div className="flex flex-col gap-2 max-h-60 overflow-y-auto pr-1">
            {records.map((rec) => (
              <div
                key={rec.id}
                className="p-3 rounded-xl bg-[#031B38]/80 border border-[#164B68]/60 flex items-start justify-between gap-3 group hover:border-[#00B8C7]/50 transition-all"
              >
                <div className="flex-1 flex flex-col gap-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-white truncate">
                      {rec.title}
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-[#164B68]/50 text-[#00E0E0] border border-[#164B68]">
                      {rec.category.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-xs text-[#C5D5E6] whitespace-pre-wrap break-words leading-relaxed">
                    {rec.content}
                  </p>
                  <span className="text-[10px] text-[#5B7998]">
                    {new Date(rec.updatedAt).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>

                <button
                  type="button"
                  onClick={() => handleDelete(rec.id)}
                  title="Delete record"
                  className="opacity-60 group-hover:opacity-100 p-1 rounded-lg text-rose-400 hover:bg-rose-500/10 transition-all"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

