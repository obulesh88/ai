import React, { useState } from 'react';
import { Settings } from '../../types';
import { Settings as SettingsIcon, Save, RefreshCw, Shield, User, Volume2, Globe, Check } from 'lucide-react';

interface SettingsPageProps {
  settings: Settings;
  onSaveSettings: (updates: Partial<Settings>) => void;
  availableModels: string[];
  isProbing: boolean;
  onRefreshProbe: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  settings,
  onSaveSettings,
  availableModels,
  isProbing,
  onRefreshProbe,
}) => {
  const [ollamaHost, setOllamaHost] = useState(settings.ollamaHost);
  const [model, setModel] = useState(settings.model);
  const [timeout, setTimeoutVal] = useState(settings.requestTimeout);
  const [userName, setUserName] = useState(settings.userName);
  const [assistantName, setAssistantName] = useState(settings.assistantName);
  const [workspace, setWorkspace] = useState(settings.workspacePath);
  const [approvalMode, setApprovalMode] = useState(settings.approvalMode);
  const [speechRate, setSpeechRate] = useState(settings.speechRate);
  const [autoSpeak, setAutoSpeak] = useState(settings.autoSpeak);

  const [savedAlert, setSavedAlert] = useState<string | null>(null);

  const handleSaveAll = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate names (2-24 chars, no control characters)
    if (userName.trim().length < 2 || userName.trim().length > 24) {
      setSavedAlert('User name must be between 2 and 24 characters.');
      return;
    }
    if (assistantName.trim().length < 2 || assistantName.trim().length > 24) {
      setSavedAlert('Assistant name must be between 2 and 24 characters.');
      return;
    }

    onSaveSettings({
      ollamaHost: ollamaHost.trim(),
      model,
      requestTimeout: Number(timeout),
      userName: userName.trim(),
      assistantName: assistantName.trim(),
      workspacePath: workspace.trim(),
      approvalMode,
      speechRate: Number(speechRate),
      autoSpeak,
    });

    setSavedAlert('Settings successfully saved and applied to active session.');
    setTimeout(() => setSavedAlert(null), 3500);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div>
          <div className="flex items-center gap-2">
            <SettingsIcon className="w-4 h-4 text-[#00e5ff]" />
            <h1 className="text-base font-bold tracking-wide text-[#d8f6ff]">System Settings & Identity</h1>
          </div>
          <p className="text-xs text-[#6f9bb3]">
            Configure model host, identity names, voice synthesizer, and security approval boundaries.
          </p>
        </div>

        <button
          onClick={handleSaveAll}
          className="px-4 py-2 rounded-lg bg-gradient-to-r from-[#2f6bff] to-[#00e5ff] text-[#04121a] font-bold text-xs font-mono shadow-[0_0_15px_rgba(0,229,255,0.4)] flex items-center gap-1.5 hover:opacity-90 transition-opacity"
        >
          <Save className="w-3.5 h-3.5" />
          Save Changes
        </button>
      </div>

      {savedAlert && (
        <div className="p-3 rounded-lg bg-[#28e0a6]/15 border border-[#28e0a6] text-[#28e0a6] text-xs font-mono flex items-center gap-2">
          <Check className="w-4 h-4" />
          {savedAlert}
        </div>
      )}

      {/* Main Settings Form */}
      <form onSubmit={handleSaveAll} className="flex-1 overflow-y-auto space-y-4 pr-1">
        {/* Identity Section */}
        <div className="glass-panel rounded-xl p-4 border border-[#00e5ff]/20 space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#00e5ff] uppercase">
            <User className="w-4 h-4" /> Identity Customization
          </div>
          <p className="text-xs text-[#6f9bb3]">
            Customizing names immediately updates the window title, holographic greeting, and model's instructions.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            <div className="space-y-1">
              <label className="text-[11px] font-mono text-[#6f9bb3] uppercase">Your Name (Operator)</label>
              <input
                type="text"
                value={userName}
                maxLength={24}
                onChange={e => setUserName(e.target.value)}
                className="w-full bg-[#060e1a] border border-[#00e5ff]/30 rounded-lg px-3 py-2 text-xs text-[#d8f6ff] font-mono focus:outline-none focus:border-[#00e5ff]"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-mono text-[#6f9bb3] uppercase">Assistant Name</label>
              <input
                type="text"
                value={assistantName}
                maxLength={24}
                onChange={e => setAssistantName(e.target.value)}
                className="w-full bg-[#060e1a] border border-[#00e5ff]/30 rounded-lg px-3 py-2 text-xs text-[#d8f6ff] font-mono focus:outline-none focus:border-[#00e5ff]"
              />
            </div>
          </div>
        </div>

        {/* AI Host & Model */}
        <div className="glass-panel rounded-xl p-4 border border-[#00e5ff]/20 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#00e5ff] uppercase">
              <Globe className="w-4 h-4" /> Model & Ollama Host Connection
            </div>
            <button
              type="button"
              onClick={onRefreshProbe}
              className="text-xs font-mono text-[#00e5ff] hover:underline flex items-center gap-1"
            >
              <RefreshCw className={`w-3 h-3 ${isProbing ? 'animate-spin' : ''}`} />
              Probe Endpoint
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[11px] font-mono text-[#6f9bb3] uppercase">OLLAMA / AI HOST URL</label>
              <input
                type="text"
                value={ollamaHost}
                onChange={e => setOllamaHost(e.target.value)}
                className="w-full bg-[#060e1a] border border-[#00e5ff]/30 rounded-lg px-3 py-2 text-xs text-[#d8f6ff] font-mono focus:outline-none focus:border-[#00e5ff]"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-mono text-[#6f9bb3] uppercase">Selected Active Model</label>
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                className="w-full bg-[#060e1a] border border-[#00e5ff]/30 rounded-lg px-3 py-2 text-xs text-[#00e5ff] font-mono focus:outline-none focus:border-[#00e5ff]"
              >
                {availableModels.map(m => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
            <div className="space-y-1">
              <label className="text-[11px] font-mono text-[#6f9bb3] uppercase">
                Request Timeout (seconds)
              </label>
              <input
                type="number"
                min={10}
                max={600}
                value={timeout}
                onChange={e => setTimeoutVal(Number(e.target.value))}
                className="w-full bg-[#060e1a] border border-[#00e5ff]/30 rounded-lg px-3 py-2 text-xs text-[#d8f6ff] font-mono focus:outline-none focus:border-[#00e5ff]"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-mono text-[#6f9bb3] uppercase">Approved Workspace Path</label>
              <input
                type="text"
                value={workspace}
                onChange={e => setWorkspace(e.target.value)}
                className="w-full bg-[#060e1a] border border-[#00e5ff]/30 rounded-lg px-3 py-2 text-xs text-[#d8f6ff] font-mono focus:outline-none focus:border-[#00e5ff]"
              />
            </div>
          </div>
        </div>

        {/* Security & Voice */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Security */}
          <div className="glass-panel rounded-xl p-4 border border-[#00e5ff]/20 space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#28e0a6] uppercase">
              <Shield className="w-4 h-4" /> Command Security Policy
            </div>

            <div className="space-y-2">
              {[
                { id: 'strict', label: 'Strict Approval', desc: 'Ask for confirmation on all commands and file writes.' },
                { id: 'ask_dangerous', label: 'Ask for Dangerous Actions', desc: 'Confirm destructive actions, allow safe reads.' },
                { id: 'permissive', label: 'Autonomous Permissive', desc: 'Run commands automatically in approved workspace.' },
              ].map(opt => (
                <label
                  key={opt.id}
                  className="flex items-start gap-2.5 p-2 rounded bg-[#060e1a] border border-white/5 cursor-pointer text-xs"
                >
                  <input
                    type="radio"
                    name="approvalMode"
                    value={opt.id}
                    checked={approvalMode === opt.id}
                    onChange={() => setApprovalMode(opt.id as Settings['approvalMode'])}
                    className="mt-1"
                  />
                  <div>
                    <div className="font-semibold text-[#d8f6ff]">{opt.label}</div>
                    <div className="text-[11px] text-[#6f9bb3]">{opt.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Voice & Speech */}
          <div className="glass-panel rounded-xl p-4 border border-[#00e5ff]/20 space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono font-bold text-[#7b5cff] uppercase">
              <Volume2 className="w-4 h-4" /> Speech & Audio Synthesizer
            </div>

            <div className="space-y-3 pt-1">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-semibold text-[#d8f6ff]">Auto-Speak Responses</div>
                  <div className="text-[11px] text-[#6f9bb3]">Read assistant replies aloud using Web Speech TTS.</div>
                </div>
                <input
                  type="checkbox"
                  checked={autoSpeak}
                  onChange={e => setAutoSpeak(e.target.checked)}
                  className="w-4 h-4 accent-[#00e5ff]"
                />
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-xs font-mono text-[#6f9bb3]">
                  <span>Speech Rate</span>
                  <span>{speechRate}x</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="1.8"
                  step="0.1"
                  value={speechRate}
                  onChange={e => setSpeechRate(Number(e.target.value))}
                  className="w-full accent-[#00e5ff]"
                />
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};
