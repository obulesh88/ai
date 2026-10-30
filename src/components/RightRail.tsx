import React, { useEffect, useState } from 'react';
import { SystemStats, AuditLog, TaskItem } from '../types';
import { Cpu, HardDrive, Wifi, Shield, ListTodo, Activity } from 'lucide-react';

interface RightRailProps {
  stats: SystemStats;
  auditLogs: AuditLog[];
  activeTasks: TaskItem[];
  modelName: string;
  onNavigate: (page: string) => void;
}

export const RightRail: React.FC<RightRailProps> = ({
  stats,
  auditLogs,
  activeTasks,
  modelName,
  onNavigate,
}) => {
  const [liveCpu, setLiveCpu] = useState(stats.cpu);
  const [liveMem, setLiveMem] = useState(stats.memory);
  const [netSpeed, setNetSpeed] = useState({ in: 42, out: 18 });

  // Simulate subtle real-time telemetry fluctuations
  useEffect(() => {
    const timer = setInterval(() => {
      setLiveCpu(Math.max(12, Math.min(88, stats.cpu + Math.floor((Math.random() - 0.5) * 8))));
      setLiveMem(Math.max(30, Math.min(78, stats.memory + Math.floor((Math.random() - 0.5) * 4))));
      setNetSpeed({
        in: Math.floor(Math.random() * 85 + 20),
        out: Math.floor(Math.random() * 45 + 10),
      });
    }, 2500);
    return () => clearInterval(timer);
  }, [stats]);

  return (
    <aside className="w-72 border-l border-[#00e5ff]/20 bg-[#060c16]/90 backdrop-blur-md flex flex-col shrink-0 select-none overflow-y-auto">
      {/* Header */}
      <div className="p-3 border-b border-[#00e5ff]/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-[#00e5ff] animate-pulse" />
          <span className="text-xs font-mono font-bold tracking-widest text-[#00e5ff] uppercase">
            Live Telemetry
          </span>
        </div>
        <span className="text-[10px] font-mono text-[#28e0a6] bg-[#28e0a6]/10 px-2 py-0.5 rounded border border-[#28e0a6]/30">
          HEALTHY
        </span>
      </div>

      <div className="p-3 space-y-4 text-xs font-mono">
        {/* System Hardware Gauges */}
        <div className="p-3 rounded-lg border border-[#00e5ff]/20 bg-[#0b1626]/80 space-y-3">
          <div className="text-[10px] text-[#6f9bb3] uppercase tracking-wider font-bold">
            Hardware Meters
          </div>

          {/* CPU Bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px]">
              <span className="flex items-center gap-1.5 text-[#d8f6ff]">
                <Cpu className="w-3.5 h-3.5 text-[#00e5ff]" /> CPU Core
              </span>
              <span className="text-[#00e5ff] font-semibold">{liveCpu}%</span>
            </div>
            <div className="h-1.5 w-full bg-[#04060c] rounded-full overflow-hidden border border-white/10">
              <div
                className="h-full bg-gradient-to-r from-[#2f6bff] to-[#00e5ff] transition-all duration-500 rounded-full"
                style={{ width: `${liveCpu}%` }}
              />
            </div>
          </div>

          {/* Memory Bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px]">
              <span className="flex items-center gap-1.5 text-[#d8f6ff]">
                <Activity className="w-3.5 h-3.5 text-[#7b5cff]" /> RAM Load
              </span>
              <span className="text-[#7b5cff] font-semibold">{liveMem}%</span>
            </div>
            <div className="h-1.5 w-full bg-[#04060c] rounded-full overflow-hidden border border-white/10">
              <div
                className="h-full bg-gradient-to-r from-[#2f6bff] to-[#7b5cff] transition-all duration-500 rounded-full"
                style={{ width: `${liveMem}%` }}
              />
            </div>
          </div>

          {/* Disk Bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-[11px]">
              <span className="flex items-center gap-1.5 text-[#d8f6ff]">
                <HardDrive className="w-3.5 h-3.5 text-[#28e0a6]" /> Disk Storage
              </span>
              <span className="text-[#28e0a6] font-semibold">{stats.disk}%</span>
            </div>
            <div className="h-1.5 w-full bg-[#04060c] rounded-full overflow-hidden border border-white/10">
              <div
                className="h-full bg-gradient-to-r from-[#28e0a6] to-[#00e5ff] transition-all duration-500 rounded-full"
                style={{ width: `${stats.disk}%` }}
              />
            </div>
          </div>

          {/* Network Throughput */}
          <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[10px] text-[#6f9bb3]">
            <span className="flex items-center gap-1">
              <Wifi className="w-3 h-3 text-[#00e5ff]" /> Net Stream
            </span>
            <span>
              ↓ <strong className="text-[#d8f6ff]">{netSpeed.in} KB/s</strong> ↑ <strong className="text-[#d8f6ff]">{netSpeed.out} KB/s</strong>
            </span>
          </div>
        </div>

        {/* Running Tasks Mini-HUD */}
        <div className="p-3 rounded-lg border border-[#00e5ff]/20 bg-[#0b1626]/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-[#6f9bb3] uppercase tracking-wider font-bold flex items-center gap-1.5">
              <ListTodo className="w-3.5 h-3.5 text-[#00e5ff]" /> Active Tasks
            </span>
            <button
              onClick={() => onNavigate('tasks')}
              className="text-[10px] text-[#00e5ff] hover:underline"
            >
              View All
            </button>
          </div>

          {activeTasks.length === 0 ? (
            <p className="text-[11px] text-[#6f9bb3]/70 italic py-1">No tasks in queue</p>
          ) : (
            <div className="space-y-2">
              {activeTasks.slice(0, 3).map(task => (
                <div
                  key={task.id}
                  onClick={() => onNavigate('tasks')}
                  className="p-2 rounded bg-[#04060c]/60 border border-white/5 hover:border-[#00e5ff]/40 cursor-pointer transition-all space-y-1"
                >
                  <div className="flex justify-between items-center text-[10px]">
                    <span className="text-[#00e5ff] font-bold">#{task.id}</span>
                    <span
                      className={`px-1.5 py-0.2 rounded text-[9px] ${
                        task.status === 'verified'
                          ? 'bg-[#28e0a6]/20 text-[#28e0a6]'
                          : task.status === 'running'
                          ? 'bg-[#00e5ff]/20 text-[#00e5ff]'
                          : 'bg-white/10 text-[#6f9bb3]'
                      }`}
                    >
                      {task.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#d8f6ff] truncate">{task.description}</div>
                  <div className="w-full bg-[#0a1220] h-1 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#00e5ff]"
                      style={{ width: `${task.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Security Audit Trail */}
        <div className="p-3 rounded-lg border border-[#00e5ff]/20 bg-[#0b1626]/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-[#6f9bb3] uppercase tracking-wider font-bold flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-[#28e0a6]" /> Audit Events
            </span>
            <span className="text-[9px] text-[#28e0a6]">LIVE</span>
          </div>

          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {auditLogs.slice(0, 6).map(log => (
              <div
                key={log.id}
                className="text-[10px] p-1.5 rounded bg-[#04060c]/50 border border-white/5"
              >
                <div className="flex items-center justify-between text-[#6f9bb3]">
                  <span className="text-[#00e5ff] font-semibold truncate max-w-[120px]">
                    [{log.action}]
                  </span>
                  <span className="text-[9px]">{log.timestamp}</span>
                </div>
                <div className="text-[#d8f6ff] truncate mt-0.5" title={log.detail}>
                  {log.detail}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
};
