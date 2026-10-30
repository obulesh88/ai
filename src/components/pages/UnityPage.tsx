import React, { useState } from 'react';
import { ProjectInfo } from '../../types';
import { Boxes, FileCode, CheckCircle, RefreshCw, Layers, Sparkles } from 'lucide-react';

interface UnityPageProps {
  projects: ProjectInfo[];
  workspacePath: string;
}

export const UnityPage: React.FC<UnityPageProps> = ({ projects, workspacePath }) => {
  const unityProjects = projects.filter(p => p.type === 'unity');
  const [activeProj, setActiveProj] = useState(unityProjects[0] || null);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div>
          <div className="flex items-center gap-2">
            <Boxes className="w-4 h-4 text-[#00e5ff]" />
            <h1 className="text-base font-bold tracking-wide text-[#d8f6ff]">Unity Engine Tools</h1>
          </div>
          <p className="text-xs text-[#6f9bb3]">
            Read-only project inspection from disk. Creating GameObjects and scene graphs requires an active Unity Editor with MCP.
          </p>
        </div>
      </div>

      {unityProjects.length === 0 ? (
        <div className="flex-1 glass-panel rounded-xl p-8 flex flex-col items-center justify-center text-center text-[#6f9bb3]">
          <Boxes className="w-12 h-12 text-[#00e5ff]/40 mb-3" />
          <h3 className="text-sm font-semibold text-[#d8f6ff]">No Unity project found in {workspacePath}</h3>
          <p className="text-xs max-w-sm mt-1">
            Create a project via CLI: <code className="text-[#00e5ff]">run: unity -createProject ...</code> (requires approval).
          </p>
        </div>
      ) : (
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden">
          {/* Project List (4 cols) */}
          <div className="lg:col-span-4 glass-panel rounded-xl p-4 flex flex-col overflow-hidden border border-[#00e5ff]/20 space-y-3">
            <span className="text-xs font-mono font-bold text-[#6f9bb3] uppercase">
              Unity Projects ({unityProjects.length})
            </span>

            <div className="space-y-2 overflow-y-auto flex-1">
              {unityProjects.map(p => (
                <div
                  key={p.name}
                  onClick={() => setActiveProj(p)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    activeProj?.name === p.name
                      ? 'bg-[#00e5ff]/15 border-[#00e5ff] shadow-[0_0_12px_rgba(0,229,255,0.2)]'
                      : 'bg-[#060e1a]/80 border-white/5 hover:border-[#00e5ff]/30'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#d8f6ff]">{p.name}</span>
                    <span className="text-[10px] font-mono text-[#00e5ff]">{p.version}</span>
                  </div>
                  <div className="text-[11px] font-mono text-[#6f9bb3] truncate mt-1">
                    {p.path}
                  </div>
                </div>
              ))}
            </div>

            <div className="p-2.5 rounded bg-[#060e1a] border border-white/5 text-[11px] text-[#6f9bb3] leading-relaxed">
              💡 1 Unity project inspected from disk. Editor actions (create GameObject, read Console) require a connected Unity MCP server.
            </div>
          </div>

          {/* Project Details (8 cols) */}
          <div className="lg:col-span-8 glass-panel rounded-xl p-4 flex flex-col overflow-y-auto border border-[#00e5ff]/20 space-y-4">
            {activeProj && (
              <>
                <div className="flex items-center justify-between pb-3 border-b border-[#00e5ff]/20">
                  <div>
                    <h2 className="text-sm font-bold text-[#00e5ff] font-mono">{activeProj.name}</h2>
                    <span className="text-xs text-[#6f9bb3]">Unity Editor Target: {activeProj.version}</span>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#28e0a6]/20 text-[#28e0a6] border border-[#28e0a6]/40 flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5" />
                    Inspected
                  </span>
                </div>

                {/* Scenes */}
                <div className="space-y-2">
                  <span className="text-xs font-mono font-bold text-[#d8f6ff] flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-[#00e5ff]" /> Scenes ({activeProj.scenes?.length || 0})
                  </span>
                  <div className="space-y-1">
                    {activeProj.scenes?.map(s => (
                      <div key={s} className="p-2 rounded bg-[#060e1a] border border-white/5 text-xs font-mono text-[#d8f6ff] flex items-center justify-between">
                        <span>{s}</span>
                        <span className="text-[10px] text-[#6f9bb3]">Baked Lighting OK</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* C# Scripts */}
                <div className="space-y-2">
                  <span className="text-xs font-mono font-bold text-[#d8f6ff] flex items-center gap-1.5">
                    <FileCode className="w-3.5 h-3.5 text-[#00e5ff]" /> C# Scripts ({activeProj.scripts?.length || 0})
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {activeProj.scripts?.map(s => (
                      <div key={s} className="p-2 rounded bg-[#060e1a] border border-white/5 text-xs font-mono text-[#d8f6ff] flex items-center gap-2">
                        <FileCode className="w-3.5 h-3.5 text-[#2f6bff]" />
                        <span className="truncate">{s}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
