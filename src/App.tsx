import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Store } from './services/store';
import { AiService } from './services/aiService';
import { runDiagnostics } from './services/doctor';
import { Settings, Message, MemoryItem, TaskItem, AuditLog, ProjectInfo, McpServer, NoteItem, ActionOutcome, SystemStats } from './types';

import { TopNav } from './components/TopNav';
import { Sidebar } from './components/Sidebar';
import { RightRail } from './components/RightRail';

import { ChatPage } from './components/pages/ChatPage';
import { HistoryPage } from './components/pages/HistoryPage';
import { MemoryPage } from './components/pages/MemoryPage';
import { TasksPage } from './components/pages/TasksPage';
import { GameDevPage } from './components/pages/GameDevPage';
import { UnityPage } from './components/pages/UnityPage';
import { UnrealPage } from './components/pages/UnrealPage';
import { CodingPage } from './components/pages/CodingPage';
import { DragonTigerPage } from './components/pages/DragonTigerPage';
import { DoctorPage } from './components/pages/DoctorPage';
import { PluginsPage } from './components/pages/PluginsPage';
import { SettingsPage } from './components/pages/SettingsPage';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<string>('chat');
  const [settings, setSettings] = useState<Settings>(() => Store.getSettings());
  const [messages, setMessages] = useState<Message[]>(() => Store.getMessages());
  const [memories, setMemories] = useState<MemoryItem[]>(() => Store.getMemories());
  const [tasks, setTasks] = useState<TaskItem[]>(() => Store.getTasks());
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>(() => Store.getAuditLogs());
  const [notes, setNotes] = useState<NoteItem[]>(() => Store.getNotes());
  const [projects] = useState<ProjectInfo[]>(() => Store.getProjects());
  const [mcpServers] = useState<McpServer[]>(() => Store.getMcpServers());

  // Connectivity & Model State
  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [availableModels, setAvailableModels] = useState<string[]>([
    'llama3:latest',
    'deepseek-r1:8b',
    'mistral:7b',
    'qwen2.5-coder:7b',
    'phi3:mini',
  ]);
  const [isProbing, setIsProbing] = useState<boolean>(false);
  const [doctorScore, setDoctorScore] = useState<number>(96);

  // Chat Execution State
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const [activeStreamText, setActiveStreamText] = useState<string>('');
  const [activeOutcome, setActiveOutcome] = useState<ActionOutcome | null>(null);

  // Voice State
  const [voiceActive, setVoiceActive] = useState<boolean>(settings.voiceEnabled);
  const recognitionRef = useRef<any>(null);

  // System Stats for Right Rail
  const [systemStats, setSystemStats] = useState<SystemStats>({
    cpu: 28,
    memory: 46,
    disk: 34,
    netIn: 38,
    netOut: 14,
    activeTasks: tasks.filter(t => t.status === 'running' || t.status === 'pending').length,
  });

  // Check Doctor score on boot
  useEffect(() => {
    runDiagnostics().then(res => setDoctorScore(res.score));
  }, []);

  // Probe Host
  const probeOllama = useCallback(async () => {
    setIsProbing(true);
    const result = await AiService.probeHost(settings.ollamaHost);
    setIsOnline(result.online);
    if (result.models.length > 0) {
      setAvailableModels(result.models);
    }
    setIsProbing(false);
  }, [settings.ollamaHost]);

  useEffect(() => {
    probeOllama();
  }, [probeOllama]);

  // Sync assistant name with document title
  useEffect(() => {
    document.title = `${settings.assistantName} - Local Personal AI Assistant`;
  }, [settings.assistantName]);

  // Voice Speech Recognition Setup
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    if (voiceActive) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onresult = (event: any) => {
          const transcript = event.results[event.results.length - 1][0].transcript.trim();
          if (!transcript) return;

          // Check wake word or process directly if voice active
          const lower = transcript.toLowerCase();
          const cleanPrompt = lower.replace(new RegExp(`^(hey\\s+)?${settings.assistantName.toLowerCase()}[,\\s]*`, 'i'), '').trim();

          if (cleanPrompt) {
            handleSendMessage(cleanPrompt);
          }
        };

        recognition.onerror = () => {
          // Keep listening resiliently
        };

        recognition.onend = () => {
          if (voiceActive) {
            try {
              recognition.start();
            } catch {
              // ignore
            }
          }
        };

        recognition.start();
        recognitionRef.current = recognition;
      } catch {
        // Microphone access denied or not supported
      }
    } else {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
    };
  }, [voiceActive, settings.assistantName]);

  // Voice Synthesizer Output
  const speakText = (text: string) => {
    if (!settings.autoSpeak || !('speechSynthesis' in window)) return;
    try {
      window.speechSynthesis.cancel();
      // Strip markdown code blocks before speaking
      const clean = text.replace(/```[\s\S]*?```/g, 'Code block generated.').replace(/[#*_`]/g, '');
      const utterance = new SpeechSynthesisUtterance(clean);
      utterance.rate = settings.speechRate || 1.0;
      window.speechSynthesis.speak(utterance);
    } catch {
      // ignore
    }
  };

  // Chat Send Handler
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isBusy) return;

    const userMsg: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    Store.saveMessages(nextMessages);
    Store.addAudit('chat_message', 'user_input', text.slice(0, 50), 'approved');
    setAuditLogs(Store.getAuditLogs());

    setIsBusy(true);
    setActiveStreamText('');
    setActiveOutcome(null);

    await AiService.sendMessage(text, nextMessages, {
      onChunk: chunk => {
        setActiveStreamText(chunk);
      },
      onOutcome: outcome => {
        setActiveOutcome(outcome);
      },
      onDone: (fullText, finalOutcome) => {
        const assistantMsg: Message = {
          id: `msg_${Date.now() + 1}`,
          role: 'assistant',
          content: fullText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          outcome: finalOutcome || activeOutcome || undefined,
        };
        const updated = [...nextMessages, assistantMsg];
        setMessages(updated);
        Store.saveMessages(updated);
        setIsBusy(false);
        setActiveStreamText('');
        setActiveOutcome(null);

        // Update memories and tasks if modified
        setMemories(Store.getMemories());
        setTasks(Store.getTasks());
        setAuditLogs(Store.getAuditLogs());

        // Speak aloud if enabled
        speakText(fullText);
      },
      onError: err => {
        const errorMsg: Message = {
          id: `msg_${Date.now() + 1}`,
          role: 'assistant',
          content: `⚠️ Error during model generation: ${err}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };
        const updated = [...nextMessages, errorMsg];
        setMessages(updated);
        Store.saveMessages(updated);
        setIsBusy(false);
        setActiveStreamText('');
        setActiveOutcome(null);
      },
    });
  };

  // Stop Streaming
  const handleStop = () => {
    AiService.stop();
    if (activeStreamText) {
      const assistantMsg: Message = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: activeStreamText + ' [Interrupted by user]',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        outcome: activeOutcome || undefined,
      };
      const updated = [...messages, assistantMsg];
      setMessages(updated);
      Store.saveMessages(updated);
    }
    setIsBusy(false);
    setActiveStreamText('');
    setActiveOutcome(null);
  };

  // Clear Chat
  const handleClearChat = () => {
    Store.clearMessages();
    setMessages([]);
    setAuditLogs(Store.getAuditLogs());
  };

  // Memory Handlers
  const handleAddMemory = (content: string, kind: MemoryItem['kind']) => {
    const res = Store.addMemory(content, kind);
    setMemories(Store.getMemories());
    setAuditLogs(Store.getAuditLogs());
    return res;
  };

  const handleDeleteMemory = (id: number) => {
    Store.deleteMemory(id);
    setMemories(Store.getMemories());
    setAuditLogs(Store.getAuditLogs());
  };

  const handleClearMemories = () => {
    Store.clearMemories();
    setMemories([]);
    setAuditLogs(Store.getAuditLogs());
  };

  // Task Handlers
  const handleAddTask = (desc: string) => {
    Store.addTask(desc);
    setTasks(Store.getTasks());
    setAuditLogs(Store.getAuditLogs());
  };

  const handleCancelTask = (id: number) => {
    Store.cancelTask(id);
    setTasks(Store.getTasks());
    setAuditLogs(Store.getAuditLogs());
  };

  const handleUpdateTask = (id: number, updates: Partial<TaskItem>) => {
    Store.updateTask(id, updates);
    setTasks(Store.getTasks());
    setAuditLogs(Store.getAuditLogs());
  };

  const handleDeleteTask = (id: number) => {
    Store.deleteTask(id);
    setTasks(Store.getTasks());
    setAuditLogs(Store.getAuditLogs());
  };

  // Settings Handlers
  const handleSaveSettings = (updates: Partial<Settings>) => {
    const saved = Store.saveSettings(updates);
    setSettings(saved);
    setAuditLogs(Store.getAuditLogs());
    if (updates.voiceEnabled !== undefined) {
      setVoiceActive(updates.voiceEnabled);
    }
  };

  // Note Handlers
  const handleAddNote = (title: string, category: string, content: string) => {
    Store.addNote(title, category, content);
    setNotes(Store.getNotes());
    setAuditLogs(Store.getAuditLogs());
  };

  const handleDeleteNote = (id: string) => {
    Store.deleteNote(id);
    setNotes(Store.getNotes());
  };

  const pendingTasksCount = tasks.filter(t => t.status === 'pending' || t.status === 'running').length;

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#04060c] text-[#d8f6ff] select-none font-sans">
      {/* Top Header Bar */}
      <TopNav
        settings={settings}
        isOnline={isOnline}
        activeModel={settings.model}
        onNavigate={setCurrentPage}
        onRefreshProbe={probeOllama}
        isProbing={isProbing}
        voiceActive={voiceActive}
        onToggleVoice={() => setVoiceActive(!voiceActive)}
        doctorScore={doctorScore}
      />

      {/* Main App Workspace (Sidebar + Center Content + Right Rail) */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Left Sidebar */}
        <Sidebar
          currentPage={currentPage}
          onNavigate={setCurrentPage}
          workspacePath={settings.workspacePath}
          pendingTasksCount={pendingTasksCount}
          memoryCount={memories.length}
        />

        {/* Center Workspace Pages */}
        <main className="flex-1 flex flex-col overflow-hidden bg-gradient-to-br from-[#04060c] via-[#0a1220] to-[#04060c]">
          {currentPage === 'chat' && (
            <ChatPage
              messages={messages}
              settings={settings}
              onSendMessage={handleSendMessage}
              onStop={handleStop}
              onClear={handleClearChat}
              isBusy={isBusy}
              activeStreamText={activeStreamText}
              activeOutcome={activeOutcome}
              voiceActive={voiceActive}
              onToggleVoice={() => setVoiceActive(!voiceActive)}
            />
          )}

          {currentPage === 'history' && (
            <HistoryPage
              messages={messages}
              onClearHistory={handleClearChat}
              assistantName={settings.assistantName}
              userName={settings.userName}
            />
          )}

          {currentPage === 'memory' && (
            <MemoryPage
              memories={memories}
              onAddMemory={handleAddMemory}
              onDeleteMemory={handleDeleteMemory}
              onClearMemories={handleClearMemories}
            />
          )}

          {currentPage === 'tasks' && (
            <TasksPage
              tasks={tasks}
              onAddTask={handleAddTask}
              onCancelTask={handleCancelTask}
              onUpdateTask={handleUpdateTask}
              onDeleteTask={handleDeleteTask}
            />
          )}

          {currentPage === 'gamedev' && (
            <GameDevPage
              projects={projects}
              mcpServers={mcpServers}
              workspacePath={settings.workspacePath}
              onNavigate={setCurrentPage}
            />
          )}

          {currentPage === 'unity' && (
            <UnityPage
              projects={projects}
              workspacePath={settings.workspacePath}
            />
          )}

          {currentPage === 'unreal' && (
            <UnrealPage
              projects={projects}
              workspacePath={settings.workspacePath}
            />
          )}

          {currentPage === 'coding' && <CodingPage />}

          {currentPage === 'analytics' && <DragonTigerPage />}

          {currentPage === 'doctor' && <DoctorPage />}

          {currentPage === 'plugins' && (
            <PluginsPage
              notes={notes}
              onAddNote={handleAddNote}
              onDeleteNote={handleDeleteNote}
            />
          )}

          {currentPage === 'settings' && (
            <SettingsPage
              settings={settings}
              onSaveSettings={handleSaveSettings}
              availableModels={availableModels}
              isProbing={isProbing}
              onRefreshProbe={probeOllama}
            />
          )}
        </main>

        {/* Right Rail Telemetry HUD */}
        <RightRail
          stats={{
            ...systemStats,
            activeTasks: pendingTasksCount,
          }}
          auditLogs={auditLogs}
          activeTasks={tasks}
          modelName={settings.model}
          onNavigate={setCurrentPage}
        />
      </div>
    </div>
  );
};
