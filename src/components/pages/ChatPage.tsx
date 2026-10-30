import React, { useState, useRef, useEffect } from 'react';
import { Message, Settings, ActionOutcome } from '../../types';
import { HoloAvatar } from '../HoloAvatar';
import { Send, Square, Trash2, Mic, MicOff, Copy, Check, Terminal, Sparkles, AlertCircle, ShieldAlert } from 'lucide-react';

interface ChatPageProps {
  messages: Message[];
  settings: Settings;
  onSendMessage: (text: string) => void;
  onStop: () => void;
  onClear: () => void;
  isBusy: boolean;
  activeStreamText: string;
  activeOutcome: ActionOutcome | null;
  voiceActive: boolean;
  onToggleVoice: () => void;
}

export const ChatPage: React.FC<ChatPageProps> = ({
  messages,
  settings,
  onSendMessage,
  onStop,
  onClear,
  isBusy,
  activeStreamText,
  activeOutcome,
  voiceActive,
  onToggleVoice,
}) => {
  const [input, setInput] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeStreamText]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || isBusy) return;
    setInput('');
    onSendMessage(text);
  };

  const handleSuggestion = (prompt: string) => {
    if (isBusy) return;
    onSendMessage(prompt);
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const avatarState = isBusy ? 'processing' : voiceActive ? 'speaking' : 'idle';

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Top Holographic Avatar Banner */}
      <div className="glass-panel rounded-xl p-4 flex flex-col md:flex-row items-center gap-6 relative overflow-hidden shrink-0 border border-[#00e5ff]/30 shadow-cyan-glow">
        <div className="shrink-0">
          <HoloAvatar state={avatarState} size={150} />
        </div>

        <div className="space-y-2 text-center md:text-left flex-1">
          <div className="flex items-center justify-center md:justify-start gap-2">
            <span className="text-xs font-mono text-[#00e5ff] tracking-widest uppercase bg-[#00e5ff]/10 px-2 py-0.5 rounded border border-[#00e5ff]/30">
              Interactive Holographic Core
            </span>
          </div>

          <h2 className="text-lg md:text-xl font-bold tracking-wide text-[#d8f6ff]">
            Hello <span className="text-[#00e5ff]">{settings.userName}</span>, I am{' '}
            <span className="text-[#00e5ff]">{settings.assistantName}</span>.
          </h2>

          <p className="text-xs text-[#6f9bb3] max-w-2xl leading-relaxed">
            Local autonomous workspace intelligence online. Ask me anything, or run automated routines:
          </p>

          {/* Quick Suggestion Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1 justify-center md:justify-start">
            {[
              { label: 'plan: build a snake game', icon: Terminal },
              { label: 'remember: I use Unity 2022.3', icon: Sparkles },
              { label: 'dragon tiger stats', icon: Sparkles },
              { label: 'doctor', icon: ShieldAlert },
              { label: 'gamedev', icon: Terminal },
            ].map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestion(chip.label)}
                disabled={isBusy}
                className="px-2.5 py-1 text-[11px] font-mono rounded-full bg-[#0b1626] border border-[#00e5ff]/30 text-[#d8f6ff] hover:text-[#00e5ff] hover:border-[#00e5ff] hover:bg-[#00e5ff]/10 transition-all flex items-center gap-1.5"
              >
                <chip.icon className="w-3 h-3 text-[#00e5ff]" />
                {chip.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Conversation Scroll Area */}
      <div className="flex-1 glass-panel rounded-xl p-4 flex flex-col overflow-hidden border border-[#00e5ff]/20">
        <div className="flex items-center justify-between pb-3 border-b border-[#00e5ff]/20 shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-[#00e5ff] shadow-[0_0_8px_#00e5ff]" />
            <span className="text-xs font-mono font-bold tracking-wider text-[#d8f6ff]">
              SESSION CONVERSATION
            </span>
          </div>

          <button
            onClick={onClear}
            className="px-2.5 py-1 text-xs font-mono rounded border border-white/10 text-[#6f9bb3] hover:text-[#ff4d6d] hover:border-[#ff4d6d]/40 transition-colors flex items-center gap-1.5"
            title="Clear active transcript"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear Chat
          </button>
        </div>

        {/* Message Stream List */}
        <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
          {messages.length === 0 && !activeStreamText && (
            <div className="h-full flex flex-col items-center justify-center text-center text-[#6f9bb3] space-y-2 select-none py-12">
              <div className="w-12 h-12 rounded-full border border-dashed border-[#00e5ff]/40 flex items-center justify-center text-[#00e5ff]">
                <Sparkles className="w-6 h-6 animate-pulse" />
              </div>
              <p className="text-sm font-medium text-[#d8f6ff]">Conversation buffer empty.</p>
              <p className="text-xs max-w-sm">
                Type a query below, trigger a planning sequence with <code className="text-[#00e5ff]">plan: &lt;task&gt;</code>, or record memories with <code className="text-[#00e5ff]">remember: &lt;fact&gt;</code>.
              </p>
            </div>
          )}

          {messages.map(msg => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} space-y-1.5`}
              >
                {/* Meta header */}
                <div className="flex items-center gap-2 px-1 text-[10px] font-mono text-[#6f9bb3]">
                  <span className={isUser ? 'text-[#2f6bff] font-bold' : 'text-[#00e5ff] font-bold'}>
                    {isUser ? settings.userName : settings.assistantName}
                  </span>
                  <span>{msg.timestamp}</span>
                </div>

                {/* Outcome badge if present */}
                {msg.outcome && (
                  <div
                    className={`text-[10px] font-mono px-2.5 py-1 rounded-md border flex items-center gap-1.5 ${
                      msg.outcome.status === 'refused'
                        ? 'bg-[#ff4d6d]/15 border-[#ff4d6d]/40 text-[#ff4d6d]'
                        : 'bg-[#28e0a6]/15 border-[#28e0a6]/40 text-[#28e0a6]'
                    }`}
                  >
                    <AlertCircle className="w-3 h-3" />
                    <span>[{msg.outcome.action.toUpperCase()}] {msg.outcome.target} &rarr; {msg.outcome.result}</span>
                  </div>
                )}

                {/* Bubble */}
                <div
                  className={`relative group max-w-[85%] rounded-xl p-3.5 text-xs sm:text-sm leading-relaxed ${
                    isUser
                      ? 'bg-[#0b1a2e] border border-[#2f6bff]/40 text-[#d8f6ff] rounded-tr-none'
                      : 'bg-[#0a1525]/90 border border-[#00e5ff]/30 text-[#d8f6ff] shadow-[0_0_15px_rgba(0,229,255,0.05)] rounded-tl-none'
                  }`}
                >
                  <div className="whitespace-pre-wrap font-sans space-y-2">
                    {msg.content}
                  </div>

                  {/* Copy button */}
                  {!isUser && (
                    <button
                      onClick={() => copyToClipboard(msg.content, msg.id)}
                      className="absolute top-2 right-2 p-1.5 rounded bg-[#04060c]/60 text-[#6f9bb3] hover:text-[#00e5ff] opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Copy response"
                    >
                      {copiedId === msg.id ? (
                        <Check className="w-3.5 h-3.5 text-[#28e0a6]" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  )}
                </div>
              </div>
            );
          })}

          {/* Active Streaming Response Bubble */}
          {(activeStreamText || isBusy) && (
            <div className="flex flex-col items-start space-y-1.5">
              <div className="flex items-center gap-2 px-1 text-[10px] font-mono text-[#00e5ff]">
                <span className="font-bold">{settings.assistantName}</span>
                <span className="animate-pulse">Synthesizing...</span>
              </div>

              {activeOutcome && (
                <div className="text-[10px] font-mono px-2.5 py-1 rounded-md border bg-[#28e0a6]/15 border-[#28e0a6]/40 text-[#28e0a6] flex items-center gap-1.5">
                  <AlertCircle className="w-3 h-3" />
                  <span>[{activeOutcome.action.toUpperCase()}] {activeOutcome.target}</span>
                </div>
              )}

              <div className="max-w-[85%] rounded-xl p-3.5 text-xs sm:text-sm bg-[#0a1525]/90 border border-[#00e5ff]/40 text-[#d8f6ff] rounded-tl-none shadow-cyan-glow">
                <div className="whitespace-pre-wrap font-sans">
                  {activeStreamText}
                  <span className="inline-block w-2 h-4 ml-1 bg-[#00e5ff] animate-pulse align-middle" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Composer */}
        <form onSubmit={handleSubmit} className="pt-3 border-t border-[#00e5ff]/20 flex items-center gap-2 shrink-0">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={isBusy}
            placeholder={`Message ${settings.assistantName}... (Enter to send, try: plan: ..., remember: ...)`}
            className="flex-1 bg-[#060e1a] border border-[#00e5ff]/30 focus:border-[#00e5ff] rounded-lg px-4 py-2.5 text-xs sm:text-sm text-[#d8f6ff] placeholder-[#6f9bb3]/60 focus:outline-none focus:ring-1 focus:ring-[#00e5ff] font-mono"
          />

          <button
            type="button"
            onClick={onToggleVoice}
            className={`p-2.5 rounded-lg border transition-all ${
              voiceActive
                ? 'bg-[#7b5cff]/20 border-[#7b5cff] text-[#7b5cff]'
                : 'bg-[#0b1626] border-white/10 text-[#6f9bb3] hover:text-[#d8f6ff]'
            }`}
            title="Toggle Voice Input"
          >
            {voiceActive ? <Mic className="w-4 h-4 animate-pulse" /> : <MicOff className="w-4 h-4" />}
          </button>

          {isBusy ? (
            <button
              type="button"
              onClick={onStop}
              className="px-4 py-2.5 rounded-lg bg-[#ff4d6d]/20 border border-[#ff4d6d] text-[#ff4d6d] hover:bg-[#ff4d6d]/30 font-semibold text-xs font-mono flex items-center gap-1.5"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="px-5 py-2.5 rounded-lg bg-gradient-to-r from-[#2f6bff] to-[#00e5ff] text-[#04121a] font-bold text-xs font-mono flex items-center gap-1.5 shadow-[0_0_15px_rgba(0,229,255,0.4)] disabled:opacity-40 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
            >
              <Send className="w-3.5 h-3.5" />
              Send
            </button>
          )}
        </form>
      </div>
    </div>
  );
};
