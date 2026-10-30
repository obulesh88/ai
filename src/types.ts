export type Role = 'user' | 'assistant' | 'system';

export interface ActionOutcome {
  action: string;
  target: string;
  result: string;
  status: 'success' | 'warning' | 'error' | 'approved' | 'refused';
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: string;
  outcome?: ActionOutcome;
  thinking?: string;
}

export type MemoryKind = 'fact' | 'preference' | 'project' | 'credential_refused';

export interface MemoryItem {
  id: number;
  kind: MemoryKind;
  content: string;
  timestamp: string;
}

export type TaskStatus = 'pending' | 'running' | 'verified' | 'completed' | 'cancelled' | 'failed';

export interface TaskItem {
  id: number;
  description: string;
  status: TaskStatus;
  progress: number;
  report?: string;
  verified?: boolean;
  retries?: number;
  steps: string[];
  createdAt: string;
}

export interface McpServer {
  name: string;
  command: string;
  status: 'ready' | 'command_not_found' | 'disconnected';
  tools: string[];
}

export interface ProjectInfo {
  name: string;
  path: string;
  type: 'unity' | 'unreal' | 'python' | 'generic';
  version?: string;
  scenes?: string[];
  scripts?: string[];
  modules?: string[];
  lastModified?: string;
}

export interface AuditLog {
  id: string;
  action: string;
  target: string;
  detail: string;
  status: 'approved' | 'refused' | 'info';
  timestamp: string;
}

export interface SystemStats {
  cpu: number;
  memory: number;
  disk: number;
  netIn: number;
  netOut: number;
  activeTasks: number;
}

export interface Settings {
  ollamaHost: string;
  model: string;
  requestTimeout: number;
  userName: string;
  assistantName: string;
  workspacePath: string;
  approvalMode: 'strict' | 'ask_dangerous' | 'permissive';
  voiceEnabled: boolean;
  speechRate: number;
  autoSpeak: boolean;
  theme: string;
}

export interface DoctorCheck {
  id: string;
  category: string;
  name: string;
  status: 'pass' | 'warn' | 'fail';
  detail: string;
  recommendation?: string;
}

export interface DragonTigerRound {
  id: number;
  dragonCard: { rank: string; value: number; suit: string };
  tigerCard: { rank: string; value: number; suit: string };
  winner: 'dragon' | 'tiger' | 'tie';
  timestamp: string;
}

export interface NoteItem {
  id: string;
  title: string;
  content: string;
  category: string;
  updatedAt: string;
}
