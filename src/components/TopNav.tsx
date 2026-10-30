import React from 'react';
import { Settings as SettingsType } from '../types';
import { Settings, Activity, Mic, MicOff, RefreshCw, Cpu, ShieldCheck } from 'lucide-react';

interface TopNavProps {
  settings: SettingsType;
  isOnline: boolean;
  activeModel: string;
  onNavigate: (page: string) => void;
  onRefreshProbe: () => void;
  isProbing: boolean;
  voiceActive: boolean;
  onToggleVoice: () => void;
  doctorScore: number;
}

export const TopNav: React.FC<TopNavProps> = ({
  settings,
  isOnline,
  activeModel,
  onNavigate,
  onRefreshProbe,
  isProbing,
  voiceActive,
  onToggleVoice,
  doctorScore,
}) => {
  return (
    <header className="h-16 px-5 border-b border-[#00e5ff]/20 bg-[#0a1220]/80 backdrop-blur-md flex items-center justify-between select-none z-30 shrink-0">
      {/* Brand & Logo */}
      <div className="flex items-center gap-3.5">
        <div className="relative w-9 h-9 flex items-center justify-center cursor-pointer" onClick={() => onNavigate('chat')}>
          <svg className="w-full h-full text-[#00e5ff] drop-shadow-[0_0_8px_rgba(0,229,255,0.6)]" viewBox="0 0 100 100">
            <polygon
              points="50,6 90,28 90,72 50,94 10,72 10,28"
              fill="rgba(10, 22, 38, 0.9)"
              stroke="#00e5ff"
              strokeWidth="5"
            />
            <polygon
              points="50,22 75,36 75,64 50,78 25,64 25,36"
              fill="none"
              stroke="#2f6bff"
              strokeWidth="3"
              strokeDasharray="4 4"
            />
            <circle cx="50" cy="50" r="10" fill="#00e5ff" />
          </svg>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-[0.25em] text-[#00e5ff] drop-shadow-[0_0_10px_rgba(0,229,255,0.4)]">
              {settings.assistantName}
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#00e5ff]/10 text-[#00e5ff] border border-[#00e5ff]/30">
              v2.4
            </span>
          </div>
          <p className="text-[10px] text-[#6f9bb3] tracking-[0.18em] uppercase font-mono">
            Autonomous Cyber Core
          </p>
        </div>
      </div>

      {/* Center Status Cluster */}
      <div className="hidden md:flex items-center gap-4 text-xs font-mono">
        {/* Online / Offline probe pill */}
        <div
          onClick={onRefreshProbe}
          title="Click to re-probe AI host endpoint"
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full border cursor-pointer transition-all hover:bg-white/5 ${
            isOnline
              ? 'bg-[#28e0a6]/10 border-[#28e0a6]/40 text-[#28e0a6]'
              : 'bg-[#ffc457]/10 border-[#ffc457]/40 text-[#ffc457]'
          }`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              isOnline ? 'bg-[#28e0a6] shadow-[0_0_8px_#28e0a6]' : 'bg-[#ffc457] shadow-[0_0_8px_#ffc457]'
            }`}
          />
          <span className="font-semibold">{isOnline ? 'ONLINE' : 'HYBRID KERNEL'}</span>
          <RefreshCw className={`w-3 h-3 ml-0.5 opacity-60 ${isProbing ? 'animate-spin' : ''}`} />
        </div>

        {/* Model display */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0b1626] border border-[#00e5ff]/20 text-[#d8f6ff]">
          <Cpu className="w-3.5 h-3.5 text-[#00e5ff]" />
          <span className="text-[#6f9bb3]">MODEL:</span>
          <span className="text-[#00e5ff] font-semibold">{activeModel}</span>
        </div>

        {/* Ollama Host URL */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0b1626]/70 border border-white/10 text-[#6f9bb3]">
          <span className="text-[11px] truncate max-w-[190px]">{settings.ollamaHost}</span>
        </div>

        {/* Doctor Health badge */}
        <button
          onClick={() => onNavigate('doctor')}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-[#0b1626] border border-[#00e5ff]/20 text-[#d8f6ff] hover:border-[#00e5ff]/50 transition-colors"
          title="System Doctor Diagnostics"
        >
          <ShieldCheck className="w-3.5 h-3.5 text-[#28e0a6]" />
          <span>HEALTH:</span>
          <span className="text-[#28e0a6] font-bold">{doctorScore}%</span>
        </button>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5">
        {/* Voice Assistant Toggle */}
        <button
          onClick={onToggleVoice}
          className={`p-2 rounded-lg border transition-all flex items-center gap-1.5 text-xs font-mono ${
            voiceActive
              ? 'bg-[#7b5cff]/20 border-[#7b5cff] text-[#7b5cff] shadow-[0_0_12px_rgba(123,92,255,0.4)]'
              : 'bg-[#0b1626] border-[#00e5ff]/20 text-[#6f9bb3] hover:text-[#d8f6ff] hover:border-[#00e5ff]/40'
          }`}
          title={voiceActive ? 'Listening for wake word "Hey HEMA"... (Click to mute)' : 'Enable Voice Assistant & Wake Word'}
        >
          {voiceActive ? <Mic className="w-4 h-4 animate-pulse" /> : <MicOff className="w-4 h-4" />}
          <span className="hidden sm:inline">{voiceActive ? 'VOICE ON' : 'VOICE OFF'}</span>
        </button>

        {/* Settings button */}
        <button
          onClick={() => onNavigate('settings')}
          className="p-2 rounded-lg bg-[#0b1626] border border-[#00e5ff]/20 text-[#6f9bb3] hover:text-[#00e5ff] hover:border-[#00e5ff]/60 hover:shadow-[0_0_12px_rgba(0,229,255,0.2)] transition-all"
          title="Open Settings"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
