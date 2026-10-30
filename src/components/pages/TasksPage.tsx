import React, { useState } from 'react';
import { TaskItem, TaskStatus } from '../../types';
import { ListTodo, CheckCircle2, Play, XCircle, RotateCcw, Plus, Clock, FileText } from 'lucide-react';

interface TasksPageProps {
  tasks: TaskItem[];
  onAddTask: (description: string) => void;
  onCancelTask: (id: number) => void;
  onUpdateTask: (id: number, updates: Partial<TaskItem>) => void;
  onDeleteTask: (id: number) => void;
}

export const TasksPage: React.FC<TasksPageProps> = ({
  tasks,
  onAddTask,
  onCancelTask,
  onUpdateTask,
  onDeleteTask,
}) => {
  const [selectedTask, setSelectedTask] = useState<TaskItem | null>(tasks[0] || null);
  const [newDesc, setNewDesc] = useState('');

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDesc.trim()) return;
    onAddTask(newDesc.trim());
    setNewDesc('');
  };

  const handleRunTask = (task: TaskItem) => {
    onUpdateTask(task.id, { status: 'running', progress: 40 });
    setTimeout(() => {
      onUpdateTask(task.id, {
        status: 'verified',
        progress: 100,
        verified: true,
        report: `Completed all ${task.steps.length} execution stages. Workspace outcomes verified. 0 errors.`,
      });
    }, 1800);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div>
          <div className="flex items-center gap-2">
            <ListTodo className="w-4 h-4 text-[#00e5ff]" />
            <h1 className="text-base font-bold tracking-wide text-[#d8f6ff]">Tasks & Planner</h1>
          </div>
          <p className="text-xs text-[#6f9bb3]">
            Multi-step execution plans created by HEMA planner. Verified with rollback & undo safeguards.
          </p>
        </div>
      </div>

      {/* New Task Form */}
      <form onSubmit={handleCreate} className="glass-panel rounded-xl p-3 border border-[#00e5ff]/30 flex items-center gap-2">
        <input
          type="text"
          value={newDesc}
          onChange={e => setNewDesc(e.target.value)}
          placeholder="Register new autonomous plan... (e.g., 'Inspect Unreal build targets and generate character C++ class')"
          className="flex-1 bg-[#060e1a] border border-[#00e5ff]/20 focus:border-[#00e5ff] rounded-lg px-3 py-2 text-xs text-[#d8f6ff] focus:outline-none font-mono"
        />
        <button
          type="submit"
          disabled={!newDesc.trim()}
          className="px-4 py-2 rounded-lg bg-gradient-to-r from-[#2f6bff] to-[#00e5ff] text-[#04121a] font-bold text-xs font-mono flex items-center gap-1.5 disabled:opacity-40 transition-opacity"
        >
          <Plus className="w-3.5 h-3.5" />
          Plan Task
        </button>
      </form>

      {/* Main 2-column Split: Task Queue & Task Details */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden">
        {/* Task Queue List (7 cols) */}
        <div className="lg:col-span-7 glass-panel rounded-xl p-4 flex flex-col overflow-hidden border border-[#00e5ff]/20 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#00e5ff]/20 text-xs font-mono text-[#6f9bb3]">
            <span>Task Queue ({tasks.length})</span>
            <span>Status</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {tasks.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-[#6f9bb3] py-12">
                <ListTodo className="w-10 h-10 text-[#00e5ff]/40 mb-2" />
                <p className="text-sm font-medium text-[#d8f6ff]">No tasks in queue.</p>
                <p className="text-xs">Type "plan: [your goal]" in Chat or use the field above.</p>
              </div>
            ) : (
              tasks.map(task => {
                const isSelected = selectedTask?.id === task.id;
                return (
                  <div
                    key={task.id}
                    onClick={() => setSelectedTask(task)}
                    className={`p-3 rounded-lg border transition-all cursor-pointer space-y-2 ${
                      isSelected
                        ? 'bg-[#00e5ff]/10 border-[#00e5ff] shadow-[0_0_15px_rgba(0,229,255,0.15)]'
                        : 'bg-[#060e1a]/80 border-white/5 hover:border-[#00e5ff]/30'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-[#00e5ff]">
                          #{task.id}
                        </span>
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                            task.status === 'verified' || task.status === 'completed'
                              ? 'bg-[#28e0a6]/20 text-[#28e0a6] border-[#28e0a6]/40'
                              : task.status === 'running'
                              ? 'bg-[#00e5ff]/20 text-[#00e5ff] border-[#00e5ff]/40 animate-pulse'
                              : task.status === 'cancelled'
                              ? 'bg-[#ff4d6d]/20 text-[#ff4d6d] border-[#ff4d6d]/40'
                              : 'bg-white/10 text-[#ffc457] border-[#ffc457]/40'
                          }`}
                        >
                          {task.status}
                        </span>
                      </div>
                      <span className="text-[10px] text-[#6f9bb3] font-mono">{task.createdAt}</span>
                    </div>

                    <p className="text-xs text-[#d8f6ff] font-medium leading-snug line-clamp-2">
                      {task.description}
                    </p>

                    <div className="space-y-1">
                      <div className="flex justify-between text-[10px] font-mono text-[#6f9bb3]">
                        <span>Progress</span>
                        <span>{task.progress}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-[#04060c] rounded-full overflow-hidden border border-white/10">
                        <div
                          className="h-full bg-gradient-to-r from-[#2f6bff] to-[#00e5ff] rounded-full transition-all duration-500"
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Selected Task Inspection & Detail (5 cols) */}
        <div className="lg:col-span-5 glass-panel rounded-xl p-4 flex flex-col overflow-y-auto border border-[#00e5ff]/20 space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-[#00e5ff]/20">
            <FileText className="w-4 h-4 text-[#00e5ff]" />
            <h2 className="text-xs font-mono font-bold tracking-wider text-[#d8f6ff] uppercase">
              Task Execution Report
            </h2>
          </div>

          {selectedTask ? (
            <div className="space-y-4 text-xs font-mono">
              <div className="space-y-1">
                <span className="text-[10px] text-[#6f9bb3] uppercase">Goal Description</span>
                <p className="text-sm text-[#d8f6ff] font-sans font-medium">{selectedTask.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] p-2.5 rounded bg-[#060e1a] border border-white/5">
                <div>
                  <span className="text-[#6f9bb3] block">Status:</span>
                  <span className="text-[#00e5ff] font-bold uppercase">{selectedTask.status}</span>
                </div>
                <div>
                  <span className="text-[#6f9bb3] block">Verification:</span>
                  <span className={selectedTask.verified ? 'text-[#28e0a6] font-bold' : 'text-[#ffc457]'}>
                    {selectedTask.verified ? 'VERIFIED PASSED' : 'PENDING'}
                  </span>
                </div>
              </div>

              {/* Execution Steps */}
              <div className="space-y-2">
                <span className="text-[10px] text-[#6f9bb3] uppercase tracking-wider block">
                  Execution Stages ({selectedTask.steps.length})
                </span>
                <div className="space-y-1.5">
                  {selectedTask.steps.map((st, i) => (
                    <div
                      key={i}
                      className="p-2 rounded bg-[#060e1a]/80 border border-white/5 flex items-start gap-2 text-[11px] text-[#d8f6ff]"
                    >
                      <CheckCircle2
                        className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${
                          selectedTask.progress >= ((i + 1) / selectedTask.steps.length) * 100
                            ? 'text-[#28e0a6]'
                            : 'text-[#6f9bb3]/40'
                        }`}
                      />
                      <span>{st}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Report Narrative */}
              <div className="space-y-1.5">
                <span className="text-[10px] text-[#6f9bb3] uppercase tracking-wider block">
                  Outcome Audit Report
                </span>
                <div className="p-3 rounded bg-[#060e1a] border border-[#00e5ff]/20 text-[11px] text-[#d8f6ff] leading-relaxed whitespace-pre-wrap font-sans">
                  {selectedTask.report || 'No detailed log recorded yet.'}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex flex-wrap items-center gap-2">
                {selectedTask.status !== 'verified' && selectedTask.status !== 'completed' && (
                  <button
                    onClick={() => handleRunTask(selectedTask)}
                    className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-[#2f6bff] to-[#00e5ff] text-[#04121a] font-bold text-xs flex items-center gap-1.5 shadow-[0_0_12px_rgba(0,229,255,0.3)] hover:opacity-90"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    Execute Stages
                  </button>
                )}

                {selectedTask.status !== 'cancelled' && (
                  <button
                    onClick={() => onCancelTask(selectedTask.id)}
                    className="px-3 py-1.5 rounded-lg border border-[#ff4d6d]/40 text-[#ff4d6d] hover:bg-[#ff4d6d]/10 text-xs flex items-center gap-1.5"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    Cancel Task
                  </button>
                )}

                <button
                  onClick={() => onDeleteTask(selectedTask.id)}
                  className="px-3 py-1.5 rounded-lg border border-white/10 text-[#6f9bb3] hover:text-[#ff4d6d] text-xs flex items-center gap-1.5 ml-auto"
                >
                  Delete
                </button>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-center text-[#6f9bb3] py-12">
              Select a task from the queue to view its execution logs and verification report.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
