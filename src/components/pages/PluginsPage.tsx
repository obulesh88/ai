import React, { useState } from 'react';
import { NoteItem } from '../../types';
import { Puzzle, FileText, Plus, Trash2, CheckCircle2, BookOpen } from 'lucide-react';

interface PluginsPageProps {
  notes: NoteItem[];
  onAddNote: (title: string, category: string, content: string) => void;
  onDeleteNote: (id: string) => void;
}

export const PluginsPage: React.FC<PluginsPageProps> = ({
  notes,
  onAddNote,
  onDeleteNote,
}) => {
  const [plugins, setPlugins] = useState([
    { id: 'note_taker', name: 'Note Taker Plugin', desc: 'Saves categorized technical notes and architecture guidelines.', active: true },
    { id: 'proc_monitor', name: 'Process Monitor Plugin', desc: 'Monitors background build processes and MCP socket latency.', active: true },
    { id: 'undo_journal', name: 'Undo & Rollback Journal', desc: 'Maintains reversible filesystem action records.', active: true },
    { id: 'voice_wake', name: 'Voice Wake Word Agent', desc: 'Listens for "Hey HEMA" wake phrase via Web Speech.', active: true },
  ]);

  const [newTitle, setNewTitle] = useState('');
  const [newCat, setNewCat] = useState('GameDev');
  const [newContent, setNewContent] = useState('');

  const handleCreateNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;
    onAddNote(newTitle.trim(), newCat, newContent.trim());
    setNewTitle('');
    setNewContent('');
  };

  const togglePlugin = (id: string) => {
    setPlugins(prev =>
      prev.map(p => (p.id === id ? { ...p, active: !p.active } : p))
    );
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div>
          <div className="flex items-center gap-2">
            <Puzzle className="w-4 h-4 text-[#00e5ff]" />
            <h1 className="text-base font-bold tracking-wide text-[#d8f6ff]">Plugins & Note Taker</h1>
          </div>
          <p className="text-xs text-[#6f9bb3]">
            Modular plugin architecture from plugins/ directory. Manage active plugins and project knowledge notes.
          </p>
        </div>
      </div>

      {/* Main Grid: Active Plugins (5 cols) & Note Taker (7 cols) */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden">
        {/* Plugins List (5 cols) */}
        <div className="lg:col-span-5 glass-panel rounded-xl p-4 flex flex-col overflow-hidden border border-[#00e5ff]/20 space-y-3">
          <span className="text-xs font-mono font-bold text-[#6f9bb3] uppercase pb-2 border-b border-white/10">
            Installed Plugins ({plugins.length})
          </span>

          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
            {plugins.map(p => (
              <div
                key={p.id}
                className="p-3 rounded-lg bg-[#060e1a]/80 border border-white/5 space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#d8f6ff]">{p.name}</span>
                  <button
                    onClick={() => togglePlugin(p.id)}
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border transition-colors ${
                      p.active
                        ? 'bg-[#28e0a6]/20 text-[#28e0a6] border-[#28e0a6]/40'
                        : 'bg-white/5 text-[#6f9bb3] border-white/10'
                    }`}
                  >
                    {p.active ? 'ENABLED' : 'DISABLED'}
                  </button>
                </div>
                <p className="text-[11px] text-[#6f9bb3] leading-relaxed">{p.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Note Taker (7 cols) */}
        <div className="lg:col-span-7 glass-panel rounded-xl p-4 flex flex-col overflow-hidden border border-[#00e5ff]/20 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-white/10">
            <span className="text-xs font-mono font-bold text-[#00e5ff] flex items-center gap-1.5 uppercase">
              <BookOpen className="w-4 h-4" /> Note Taker Vault ({notes.length})
            </span>
          </div>

          {/* New Note Form */}
          <form onSubmit={handleCreateNote} className="space-y-2 bg-[#060e1a] p-3 rounded-lg border border-[#00e5ff]/20">
            <div className="flex gap-2">
              <input
                type="text"
                value={newTitle}
                onChange={e => setNewTitle(e.target.value)}
                placeholder="Note Title..."
                className="flex-1 bg-[#04060c] border border-white/10 rounded px-2.5 py-1.5 text-xs text-[#d8f6ff] focus:outline-none focus:border-[#00e5ff]"
              />
              <select
                value={newCat}
                onChange={e => setNewCat(e.target.value)}
                className="bg-[#04060c] border border-white/10 rounded px-2 py-1.5 text-xs text-[#00e5ff] font-mono focus:outline-none"
              >
                <option value="GameDev">GameDev</option>
                <option value="Analytics">Analytics</option>
                <option value="System">System</option>
                <option value="General">General</option>
              </select>
            </div>
            <textarea
              value={newContent}
              onChange={e => setNewContent(e.target.value)}
              placeholder="Write note contents..."
              rows={2}
              className="w-full bg-[#04060c] border border-white/10 rounded p-2 text-xs text-[#d8f6ff] focus:outline-none focus:border-[#00e5ff] resize-none"
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={!newTitle.trim() || !newContent.trim()}
                className="px-3 py-1 rounded bg-[#00e5ff]/20 border border-[#00e5ff] text-[#00e5ff] hover:bg-[#00e5ff]/30 text-xs font-mono font-bold flex items-center gap-1 disabled:opacity-40"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Note
              </button>
            </div>
          </form>

          {/* Note List */}
          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
            {notes.map(note => (
              <div
                key={note.id}
                className="p-3 rounded-lg bg-[#060e1a]/80 border border-white/5 hover:border-[#00e5ff]/30 transition-all space-y-1.5 group"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#d8f6ff]">{note.title}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#00e5ff]/10 text-[#00e5ff] border border-[#00e5ff]/20">
                      {note.category}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-[#6f9bb3]">{note.updatedAt}</span>
                    <button
                      onClick={() => onDeleteNote(note.id)}
                      className="text-[#6f9bb3] hover:text-[#ff4d6d] opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <p className="text-xs text-[#6f9bb3] font-sans leading-relaxed whitespace-pre-wrap">
                  {note.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
