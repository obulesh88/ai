import React from 'react';
import {
  MessageSquare,
  History,
  Gamepad2,
  Boxes,
  Layers,
  Brain,
  ListTodo,
  Terminal,
  TrendingUp,
  ShieldAlert,
  Puzzle,
  Settings as SettingsIcon,
  FolderGit2,
} from 'lucide-react';

interface SidebarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
  workspacePath: string;
  pendingTasksCount: number;
  memoryCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  workspacePath,
  pendingTasksCount,
  memoryCount,
}) => {
  const navItems = [
    { id: 'chat', label: 'Chat Assistant', icon: MessageSquare, badge: null },
    { id: 'history', label: 'Chat History', icon: History, badge: null },
    { id: 'gamedev', label: 'Game Development', icon: Gamepad2, badge: 'MCP' },
    { id: 'unity', label: 'Unity Tools', icon: Boxes, badge: null },
    { id: 'unreal', label: 'Unreal Engine Tools', icon: Layers, badge: null },
    { id: 'memory', label: 'Memory Vault', icon: Brain, badge: memoryCount.toString() },
    { id: 'tasks', label: 'Tasks & Planner', icon: ListTodo, badge: pendingTasksCount > 0 ? pendingTasksCount.toString() : null },
    { id: 'coding', label: 'Coding Studio', icon: Terminal, badge: null },
    { id: 'analytics', label: 'Dragon Tiger Stats', icon: TrendingUp, badge: 'HOT' },
    { id: 'doctor', label: 'System Doctor', icon: ShieldAlert, badge: null },
    { id: 'plugins', label: 'Plugins & Notes', icon: Puzzle, badge: null },
    { id: 'settings', label: 'Settings', icon: SettingsIcon, badge: null },
  ];

  return (
    <aside className="w-64 border-r border-[#00e5ff]/20 bg-[#060c16]/90 backdrop-blur-md flex flex-col justify-between shrink-0 select-none overflow-y-auto">
      {/* Navigation Links */}
      <div className="p-3 space-y-1">
        <div className="px-3 py-2 text-[10px] font-mono tracking-widest text-[#6f9bb3] uppercase">
          Workspace Navigation
        </div>

        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all group ${
                isActive
                  ? 'bg-[#00e5ff]/15 text-[#00e5ff] border-l-2 border-[#00e5ff] font-semibold shadow-[0_0_15px_rgba(0,229,255,0.15)]'
                  : 'text-[#6f9bb3] hover:text-[#d8f6ff] hover:bg-white/5 border-l-2 border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`w-4 h-4 transition-transform group-hover:scale-110 ${
                    isActive ? 'text-[#00e5ff]' : 'text-[#6f9bb3]'
                  }`}
                />
                <span className="truncate">{item.label}</span>
              </div>

              {item.badge && (
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                    item.badge === 'HOT'
                      ? 'bg-[#ff4d6d]/20 text-[#ff4d6d] border border-[#ff4d6d]/40'
                      : isActive
                      ? 'bg-[#00e5ff]/20 text-[#00e5ff]'
                      : 'bg-white/10 text-[#6f9bb3]'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Session Info Box */}
      <div className="p-3 m-3 rounded-lg border border-[#00e5ff]/20 bg-[#0b1626]/80 text-[11px] font-mono space-y-2">
        <div className="flex items-center gap-1.5 text-[#00e5ff]">
          <FolderGit2 className="w-3.5 h-3.5" />
          <span className="font-semibold uppercase tracking-wider text-[10px]">Active Session</span>
        </div>
        <div className="text-[#6f9bb3] truncate" title={workspacePath}>
          Root: <span className="text-[#d8f6ff]">{workspacePath}</span>
        </div>
        <div className="flex items-center justify-between pt-1 border-t border-white/10 text-[10px] text-[#6f9bb3]">
          <span>Unfinished Tasks:</span>
          <span className={`font-bold ${pendingTasksCount > 0 ? 'text-[#ffc457]' : 'text-[#28e0a6]'}`}>
            {pendingTasksCount}
          </span>
        </div>
      </div>
    </aside>
  );
};
