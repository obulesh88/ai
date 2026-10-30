import React, { useState } from 'react';
import { MemoryItem, MemoryKind } from '../../types';
import { Brain, Search, Trash2, Plus, ShieldCheck, AlertTriangle } from 'lucide-react';

interface MemoryPageProps {
  memories: MemoryItem[];
  onAddMemory: (content: string, kind: MemoryKind) => { success: boolean; message: string };
  onDeleteMemory: (id: number) => void;
  onClearMemories: () => void;
}

export const MemoryPage: React.FC<MemoryPageProps> = ({
  memories,
  onAddMemory,
  onDeleteMemory,
  onClearMemories,
}) => {
  const [search, setSearch] = useState('');
  const [selectedKind, setSelectedKind] = useState<string>('all');
  const [newContent, setNewContent] = useState('');
  const [newKind, setNewKind] = useState<MemoryKind>('fact');
  const [feedback, setFeedback] = useState<{ message: string; isError: boolean } | null>(null);

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContent.trim()) return;

    const res = onAddMemory(newContent.trim(), newKind);
    setFeedback({ message: res.message, isError: !res.success });
    if (res.success) {
      setNewContent('');
    }
    setTimeout(() => setFeedback(null), 4000);
  };

  const filtered = memories.filter(m => {
    const matchesSearch =
      m.content.toLowerCase().includes(search.toLowerCase()) ||
      m.kind.toLowerCase().includes(search.toLowerCase());
    const matchesKind = selectedKind === 'all' || m.kind === selectedKind;
    return matchesSearch && matchesKind;
  });

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div>
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-[#00e5ff]" />
            <h1 className="text-base font-bold tracking-wide text-[#d8f6ff]">Memory Vault</h1>
          </div>
          <p className="text-xs text-[#6f9bb3]">
            Long-term persistent memory table. Enforces zero-credential policy: API keys & secrets are strictly rejected.
          </p>
        </div>

        <button
          onClick={onClearMemories}
          disabled={memories.length === 0}
          className="px-3 py-1.5 rounded-lg border border-[#ff4d6d]/40 text-[#ff4d6d] hover:bg-[#ff4d6d]/10 text-xs font-mono flex items-center gap-1.5 disabled:opacity-40 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
          Purge Vault
        </button>
      </div>

      {/* Add Memory Form */}
      <form onSubmit={handleCreate} className="glass-panel rounded-xl p-3 border border-[#00e5ff]/30 space-y-2">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
          <select
            value={newKind}
            onChange={e => setNewKind(e.target.value as MemoryKind)}
            className="bg-[#060e1a] border border-[#00e5ff]/30 text-xs font-mono text-[#00e5ff] rounded-lg px-2.5 py-2 focus:outline-none"
          >
            <option value="fact">Fact</option>
            <option value="preference">Preference</option>
            <option value="project">Project Note</option>
          </select>

          <input
            type="text"
            value={newContent}
            onChange={e => setNewContent(e.target.value)}
            placeholder="Add new persistent memory... (e.g., 'I prefer Cascadia Mono for coding')"
            className="flex-1 bg-[#060e1a] border border-[#00e5ff]/20 focus:border-[#00e5ff] rounded-lg px-3 py-2 text-xs text-[#d8f6ff] focus:outline-none font-mono"
          />

          <button
            type="submit"
            disabled={!newContent.trim()}
            className="px-4 py-2 rounded-lg bg-[#00e5ff]/20 border border-[#00e5ff] text-[#00e5ff] hover:bg-[#00e5ff]/30 font-bold text-xs font-mono flex items-center justify-center gap-1.5 disabled:opacity-40 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Store Memory
          </button>
        </div>

        {feedback && (
          <div
            className={`text-xs font-mono p-2 rounded border flex items-center gap-2 ${
              feedback.isError
                ? 'bg-[#ff4d6d]/20 border-[#ff4d6d] text-[#ff4d6d]'
                : 'bg-[#28e0a6]/20 border-[#28e0a6] text-[#28e0a6]'
            }`}
          >
            {feedback.isError ? <AlertTriangle className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
            {feedback.message}
          </div>
        )}
      </form>

      {/* Filters & Search */}
      <div className="glass-panel rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-3.5 h-3.5 text-[#6f9bb3] absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search memory records..."
            className="w-full bg-[#060e1a] border border-[#00e5ff]/20 focus:border-[#00e5ff] rounded-lg pl-9 pr-3 py-1.5 text-xs text-[#d8f6ff] focus:outline-none font-mono"
          />
        </div>

        <div className="flex items-center gap-2">
          {['all', 'fact', 'preference', 'project'].map(k => (
            <button
              key={k}
              onClick={() => setSelectedKind(k)}
              className={`px-2.5 py-1 text-[11px] font-mono rounded border capitalize transition-all ${
                selectedKind === k
                  ? 'bg-[#00e5ff]/20 border-[#00e5ff] text-[#00e5ff] font-bold'
                  : 'border-white/10 text-[#6f9bb3] hover:text-[#d8f6ff]'
              }`}
            >
              {k}
            </button>
          ))}
        </div>

        <span className="text-xs font-mono text-[#6f9bb3]">
          {filtered.length} of {memories.length} memories
        </span>
      </div>

      {/* Memory Cards */}
      <div className="flex-1 glass-panel rounded-xl p-4 overflow-y-auto space-y-2.5 border border-[#00e5ff]/20">
        {filtered.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-[#6f9bb3] py-12">
            <Brain className="w-10 h-10 text-[#00e5ff]/40 mb-2" />
            <p className="text-sm font-medium text-[#d8f6ff]">No memory records matching search.</p>
            <p className="text-xs">Try saying "remember: [something]" in chat or use the form above.</p>
          </div>
        ) : (
          filtered.map(mem => (
            <div
              key={mem.id}
              className="p-3 rounded-lg bg-[#060e1a]/80 border border-white/5 hover:border-[#00e5ff]/40 transition-all flex items-start justify-between gap-4 group"
            >
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-[#00e5ff]">#{mem.id}</span>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                      mem.kind === 'preference'
                        ? 'bg-[#7b5cff]/20 text-[#7b5cff] border-[#7b5cff]/40'
                        : mem.kind === 'project'
                        ? 'bg-[#28e0a6]/20 text-[#28e0a6] border-[#28e0a6]/40'
                        : 'bg-[#2f6bff]/20 text-[#00e5ff] border-[#00e5ff]/40'
                    }`}
                  >
                    {mem.kind}
                  </span>
                  <span className="text-[10px] text-[#6f9bb3]">{mem.timestamp}</span>
                </div>

                <p className="text-xs text-[#d8f6ff] leading-relaxed font-sans">{mem.content}</p>
              </div>

              <button
                onClick={() => onDeleteMemory(mem.id)}
                className="p-1.5 rounded text-[#6f9bb3] hover:text-[#ff4d6d] hover:bg-[#ff4d6d]/10 opacity-0 group-hover:opacity-100 transition-opacity"
                title={`Delete Memory #${mem.id}`}
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
