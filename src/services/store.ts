import { Settings, MemoryItem, TaskItem, AuditLog, ProjectInfo, McpServer, NoteItem, Message } from '../types';

const SETTINGS_KEY = 'hema_settings_v1';
const MEMORIES_KEY = 'hema_memories_v1';
const TASKS_KEY = 'hema_tasks_v1';
const AUDIT_KEY = 'hema_audit_v1';
const MESSAGES_KEY = 'hema_messages_v1';
const NOTES_KEY = 'hema_notes_v1';

export const DEFAULT_SETTINGS: Settings = {
  ollamaHost: 'http://127.0.0.1:11434',
  model: 'llama3:latest',
  requestTimeout: 60,
  userName: 'Operator',
  assistantName: 'HEMA',
  workspacePath: './workspace',
  approvalMode: 'ask_dangerous',
  voiceEnabled: false,
  speechRate: 1.0,
  autoSpeak: false,
  theme: 'cyberpunk',
};

const INITIAL_MEMORIES: MemoryItem[] = [
  {
    id: 1,
    kind: 'preference',
    content: 'User prefers Cascadia Mono, dark cyan cyberpunk aesthetics and concise explanations.',
    timestamp: '2026-10-28 09:15:00',
  },
  {
    id: 2,
    kind: 'project',
    content: 'Default workspace set to ./workspace for Unity & Unreal projects.',
    timestamp: '2026-10-28 10:20:00',
  },
  {
    id: 3,
    kind: 'fact',
    content: 'Unity 2022.3 LTS and Unreal Engine 5.3 installed on host machine.',
    timestamp: '2026-10-29 14:02:10',
  },
  {
    id: 4,
    kind: 'preference',
    content: 'Always request user confirmation before running destructive terminal or file operations.',
    timestamp: '2026-10-30 08:00:00',
  },
];

const INITIAL_TASKS: TaskItem[] = [
  {
    id: 101,
    description: 'Inspect Unity 2022 scene hierarchy and optimize asset bundles',
    status: 'verified',
    progress: 100,
    report: 'Successfully parsed 4 scenes, verified C# compilation with 0 warnings, verified bundle assets.',
    verified: true,
    steps: ['Parse ProjectSettings.asset', 'Audit scene dependencies', 'Validate build settings', 'Verify outcome'],
    createdAt: '2026-10-29 16:30',
  },
  {
    id: 102,
    description: 'Dragon Tiger shoe statistical analysis and Big Road trend prediction',
    status: 'completed',
    progress: 100,
    report: 'Calculated 120-hand shoe metrics: Dragon 48.3%, Tiger 45.8%, Tie 5.9%. Max streak: 6.',
    verified: true,
    steps: ['Load hand history', 'Compute streak distribution', 'Generate Big Road grid', 'Calculate win edge'],
    createdAt: '2026-10-30 07:15',
  },
  {
    id: 103,
    description: 'Unreal Engine 5 C++ Character Movement Component generator',
    status: 'pending',
    progress: 25,
    report: 'Generated header template; waiting for approval to write to Source/PlayerCharacter.h.',
    verified: false,
    steps: ['Inspect .uproject', 'Create UCLASS header', 'Implement TickComponent logic', 'Run build verification'],
    createdAt: '2026-10-30 08:45',
  },
];

const INITIAL_PROJECTS: ProjectInfo[] = [
  {
    name: 'CyberpunkOdyssey',
    path: './workspace/CyberpunkOdyssey',
    type: 'unity',
    version: '2022.3.18f1',
    scenes: ['Assets/Scenes/MainCity.unity', 'Assets/Scenes/HangarBay.unity', 'Assets/Scenes/MainMenu.unity'],
    scripts: ['PlayerController.cs', 'HoloDroneAgent.cs', 'InventorySystem.cs', 'McpBridge.cs'],
    lastModified: '2026-10-30 08:12',
  },
  {
    name: 'NeonAscent_UE5',
    path: './workspace/NeonAscent_UE5',
    type: 'unreal',
    version: '5.3.2',
    modules: ['NeonAscentCore', 'NeonAudioPlugin', 'CyberNetSubsystem'],
    lastModified: '2026-10-29 20:45',
  },
  {
    name: 'HemaTools',
    path: './workspace/HemaTools',
    type: 'python',
    scripts: ['cli.py', 'inspect_assets.py', 'stats_parser.py'],
    lastModified: '2026-10-30 06:20',
  },
];

const INITIAL_MCP_SERVERS: McpServer[] = [
  {
    name: 'Unity Editor MCP',
    command: 'npx -y @modelcontextprotocol/server-unity',
    status: 'ready',
    tools: ['inspect_hierarchy', 'read_console', 'list_assets', 'get_editor_state'],
  },
  {
    name: 'Unreal Engine MCP',
    command: 'python -m unreal_mcp_bridge --port 8089',
    status: 'ready',
    tools: ['query_uproject', 'generate_cpp_class', 'list_modules', 'read_build_log'],
  },
  {
    name: 'Filesystem Workspace Guard MCP',
    command: 'mcp-server-filesystem --allow ./workspace',
    status: 'ready',
    tools: ['read_file', 'write_file_safe', 'undo_transaction', 'audit_verify'],
  },
  {
    name: 'System Process Monitor MCP',
    command: 'hema-proc-mcp',
    status: 'ready',
    tools: ['ps_snapshot', 'kill_safe', 'telemetry_stream'],
  },
];

const INITIAL_NOTES: NoteItem[] = [
  {
    id: 'n1',
    title: 'Unity MCP Setup Guide',
    category: 'GameDev',
    content: 'Launch Unity with custom command line flags: -enable-mcp-bridge -port 8090. Ensure packages are locked.',
    updatedAt: '2026-10-29 11:30',
  },
  {
    id: 'n2',
    title: 'Dragon Tiger Martingale Warning',
    category: 'Analytics',
    content: 'Due to 8:1 Tie payout and table maximum limit, pure Martingale carries asymmetric tail risk. Focus on Streak length < 5.',
    updatedAt: '2026-10-30 07:40',
  },
  {
    id: 'n3',
    title: 'HEMA Self-Update & Rollback Protocol',
    category: 'System',
    content: 'Before executing any self-update, core/undo.py creates a tar.gz snapshot of ./core and ./interface to /backups.',
    updatedAt: '2026-10-28 17:00',
  },
];

// Secret patterns for refusal
const SECRET_REGEX = /(?:password|passwd|api[_-]?key|secret|token|bearer|private[_-]?key|auth[_-]?token|credentials|aws[_-]?secret)\s*[:=]\s*['"]?[a-zA-Z0-9_\-\.]{8,}['"]?/i;

export const Store = {
  getSettings(): Settings {
    try {
      const data = localStorage.getItem(SETTINGS_KEY);
      return data ? { ...DEFAULT_SETTINGS, ...JSON.parse(data) } : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  },

  saveSettings(settings: Partial<Settings>): Settings {
    const current = this.getSettings();
    const updated = { ...current, ...settings };
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(updated));
    this.addAudit('settings_update', 'system_config', `Updated settings: ${Object.keys(settings).join(', ')}`, 'approved');
    return updated;
  },

  getMemories(): MemoryItem[] {
    try {
      const data = localStorage.getItem(MEMORIES_KEY);
      return data ? JSON.parse(data) : INITIAL_MEMORIES;
    } catch {
      return INITIAL_MEMORIES;
    }
  },

  saveMemories(memories: MemoryItem[]): void {
    localStorage.setItem(MEMORIES_KEY, JSON.stringify(memories));
  },

  addMemory(content: string, kind: MemoryItem['kind'] = 'fact'): { success: boolean; memory?: MemoryItem; message: string } {
    // Secret Refusal Check
    if (SECRET_REGEX.test(content) || content.toLowerCase().includes('sk-') || content.toLowerCase().includes('ghp_')) {
      this.addAudit('memory_refusal', 'security_guard', 'Refused to store secret/credential in long-term memory', 'refused');
      return {
        success: false,
        message: 'Security Guard refused storage: Secrets, API keys, and credentials are prohibited in memory.',
      };
    }

    const memories = this.getMemories();
    const newMemory: MemoryItem = {
      id: memories.length ? Math.max(...memories.map(m => m.id)) + 1 : 1,
      kind,
      content,
      timestamp: new Date().toISOString().replace('T', ' ').slice(0, 19),
    };
    memories.unshift(newMemory);
    this.saveMemories(memories);
    this.addAudit('memory_add', `#${newMemory.id}`, `Stored ${kind} memory: "${content.slice(0, 40)}..."`, 'approved');
    return { success: true, memory: newMemory, message: `Stored in memory as #${newMemory.id}` };
  },

  deleteMemory(id: number): boolean {
    const memories = this.getMemories();
    const filtered = memories.filter(m => m.id !== id);
    if (filtered.length !== memories.length) {
      this.saveMemories(filtered);
      this.addAudit('memory_delete', `#${id}`, 'Deleted memory from storage', 'approved');
      return true;
    }
    return false;
  },

  clearMemories(): void {
    this.saveMemories([]);
    this.addAudit('memory_clear', 'all', 'Cleared all long-term memories', 'approved');
  },

  getTasks(): TaskItem[] {
    try {
      const data = localStorage.getItem(TASKS_KEY);
      return data ? JSON.parse(data) : INITIAL_TASKS;
    } catch {
      return INITIAL_TASKS;
    }
  },

  saveTasks(tasks: TaskItem[]): void {
    localStorage.setItem(TASKS_KEY, JSON.stringify(tasks));
  },

  addTask(description: string, steps?: string[]): TaskItem {
    const tasks = this.getTasks();
    const newTask: TaskItem = {
      id: tasks.length ? Math.max(...tasks.map(t => t.id)) + 1 : 101,
      description,
      status: 'pending',
      progress: 0,
      steps: steps || ['Initialize context', 'Analyze dependencies', 'Execute command plan', 'Verify outcome'],
      createdAt: new Date().toISOString().replace('T', ' ').slice(0, 16),
      report: 'Plan registered. Ready for execution.',
    };
    tasks.unshift(newTask);
    this.saveTasks(tasks);
    this.addAudit('task_plan', `#${newTask.id}`, `Registered task plan: ${description.slice(0, 50)}`, 'approved');
    return newTask;
  },

  updateTask(id: number, updates: Partial<TaskItem>): TaskItem | null {
    const tasks = this.getTasks();
    const index = tasks.findIndex(t => t.id === id);
    if (index === -1) return null;
    tasks[index] = { ...tasks[index], ...updates };
    this.saveTasks(tasks);
    return tasks[index];
  },

  cancelTask(id: number): boolean {
    const updated = this.updateTask(id, {
      status: 'cancelled',
      report: 'Cancelled by operator via command/UI.',
    });
    if (updated) {
      this.addAudit('task_cancel', `#${id}`, 'Task execution cancelled', 'approved');
      return true;
    }
    return false;
  },

  deleteTask(id: number): boolean {
    const tasks = this.getTasks();
    const filtered = tasks.filter(t => t.id !== id);
    if (filtered.length !== tasks.length) {
      this.saveTasks(filtered);
      return true;
    }
    return false;
  },

  getAuditLogs(): AuditLog[] {
    try {
      const data = localStorage.getItem(AUDIT_KEY);
      if (data) return JSON.parse(data);
    } catch {
      // ignore
    }
    return [
      {
        id: 'aud_1',
        action: 'system_boot',
        target: 'HEMA Kernel',
        detail: 'Cyberpunk UI initialized. Subsystems online.',
        status: 'approved',
        timestamp: '10:00:02',
      },
      {
        id: 'aud_2',
        action: 'probe_ollama',
        target: 'http://127.0.0.1:11434',
        detail: 'Discovered model registry. 3 models detected.',
        status: 'approved',
        timestamp: '10:00:05',
      },
      {
        id: 'aud_3',
        action: 'security_audit',
        target: 'workspace_guard',
        detail: 'Approved safe root: ./workspace',
        status: 'approved',
        timestamp: '10:00:08',
      },
    ];
  },

  addAudit(action: string, target: string, detail: string, status: AuditLog['status'] = 'info'): void {
    const logs = this.getAuditLogs();
    const newLog: AuditLog = {
      id: `aud_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      action,
      target,
      detail,
      status,
      timestamp: new Date().toTimeString().slice(0, 8),
    };
    logs.unshift(newLog);
    if (logs.length > 100) logs.length = 100;
    localStorage.setItem(AUDIT_KEY, JSON.stringify(logs));
  },

  getMessages(): Message[] {
    try {
      const data = localStorage.getItem(MESSAGES_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  },

  saveMessages(messages: Message[]): void {
    localStorage.setItem(MESSAGES_KEY, JSON.stringify(messages));
  },

  clearMessages(): void {
    localStorage.removeItem(MESSAGES_KEY);
    this.addAudit('chat_clear', 'transcript', 'Cleared chat history transcript', 'approved');
  },

  getProjects(): ProjectInfo[] {
    return INITIAL_PROJECTS;
  },

  getMcpServers(): McpServer[] {
    return INITIAL_MCP_SERVERS;
  },

  getNotes(): NoteItem[] {
    try {
      const data = localStorage.getItem(NOTES_KEY);
      return data ? JSON.parse(data) : INITIAL_NOTES;
    } catch {
      return INITIAL_NOTES;
    }
  },

  saveNotes(notes: NoteItem[]): void {
    localStorage.setItem(NOTES_KEY, JSON.stringify(notes));
  },

  addNote(title: string, category: string, content: string): NoteItem {
    const notes = this.getNotes();
    const newNote: NoteItem = {
      id: `note_${Date.now()}`,
      title,
      category,
      content,
      updatedAt: new Date().toISOString().replace('T', ' ').slice(0, 16),
    };
    notes.unshift(newNote);
    this.saveNotes(notes);
    this.addAudit('plugin_note', newNote.id, `Created note: "${title}"`, 'approved');
    return newNote;
  },

  deleteNote(id: string): void {
    const notes = this.getNotes().filter(n => n.id !== id);
    this.saveNotes(notes);
  },
};
