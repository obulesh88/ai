import React, { useState } from 'react';
import { Message } from '../../types';
import { History, Search, Trash2, ArrowUpDown, User, Bot } from 'lucide-react';

interface HistoryPageProps {
  messages: Message[];
  onClearHistory: () => void;
  assistantName: string;
  userName: string;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({
  messages,
  onClearHistory,
  assistantName,
  userName,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = messages.filter(
    m =>
      m.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div>
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-[#00e5ff]" />
            <h1 className="text-base font-bold tracking-wide text-[#d8f6ff]">Chat History</h1>
          </div>
          <p className="text-xs text-[#6f9bb3]">
            Conversation turns stored in local persistent memory. Complete audit records preserved.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onClearHistory}
            disabled={messages.length === 0}
            className="px-3 py-1.5 rounded-lg border border-[#ff4d6d]/40 text-[#ff4d6d] hover:bg-[#ff4d6d]/10 text-xs font-mono flex items-center gap-1.5 disabled:opacity-40 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear All History
          </button>
        </div>
      </div>

      {/* Search & Stats Bar */}
      <div className="glass-panel rounded-xl p-3 flex items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div className="relative flex-1 max-w-md">
          <Search className="w-3.5 h-3.5 text-[#6f9bb3] absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            placeholder="Search transcripts..."
            className="w-full bg-[#060e1a] border border-[#00e5ff]/20 focus:border-[#00e5ff] rounded-lg pl-9 pr-3 py-1.5 text-xs text-[#d8f6ff] focus:outline-none font-mono"
          />
        </div>

        <span className="text-xs font-mono text-[#6f9bb3]">
          Showing <strong className="text-[#00e5ff]">{filtered.length}</strong> of{' '}
          <strong className="text-[#d8f6ff]">{messages.length}</strong> stored messages
        </span>
      </div>

      {/* Messages List */}
      <div className="flex-1 glass-panel rounded-xl p-4 overflow-y-auto space-y-3 border border-[#00e5ff]/20">
        {filtered.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-[#6f9bb3] py-12">
            <History className="w-10 h-10 text-[#00e5ff]/40 mb-2" />
            <p className="text-sm font-medium text-[#d8f6ff]">No conversation history found.</p>
            <p className="text-xs">Say something in the Chat Assistant to record persistent dialogue.</p>
          </div>
        ) : (
          filtered.map(msg => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id}
                className="p-3 rounded-lg bg-[#060e1a]/80 border border-white/5 hover:border-[#00e5ff]/30 transition-all space-y-1.5"
              >
                <div className="flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    {isUser ? (
                      <span className="flex items-center gap-1 text-[#2f6bff] font-semibold">
                        <User className="w-3.5 h-3.5" /> {userName}
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-[#00e5ff] font-semibold">
                        <Bot className="w-3.5 h-3.5" /> {assistantName}
                      </span>
                    )}
                    <span className="text-[10px] text-[#6f9bb3] px-1.5 py-0.2 rounded bg-white/5">
                      {msg.role.toUpperCase()}
                    </span>
                  </div>
                  <span className="text-[11px] text-[#6f9bb3]">{msg.timestamp}</span>
                </div>

                <div className="text-xs text-[#d8f6ff] whitespace-pre-wrap font-sans pl-5 border-l-2 border-[#00e5ff]/20">
                  {msg.content}
                </div>

                {msg.outcome && (
                  <div className="text-[10px] font-mono text-[#28e0a6] pl-5">
                    [{msg.outcome.action}] &rarr; {msg.outcome.result}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
