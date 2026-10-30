import React, { useState } from 'react';
import { ProjectInfo, McpServer } from '../../types';
import { Gamepad2, Boxes, Layers, Terminal, RefreshCw, Wrench, CheckCircle, AlertTriangle, Code2 } from 'lucide-react';

interface GameDevPageProps {
  projects: ProjectInfo[];
  mcpServers: McpServer[];
  workspacePath: string;
  onNavigate: (page: string) => void;
}

export const GameDevPage: React.FC<GameDevPageProps> = ({
  projects,
  mcpServers,
  workspacePath,
  onNavigate,
}) => {
  const [showToolsModal, setShowToolsModal] = useState(false);
  const [selectedTool, setSelectedTool] = useState<string>('scene');

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div>
          <div className="flex items-center gap-2">
            <Gamepad2 className="w-4 h-4 text-[#00e5ff]" />
            <h1 className="text-base font-bold tracking-wide text-[#d8f6ff]">Game Development</h1>
          </div>
          <p className="text-xs text-[#6f9bb3]">
            Projects discovered inside approved workspace ({workspacePath}). Engine automation via MCP bridges.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowToolsModal(true)}
            className="px-3 py-1.5 rounded-lg bg-[#00e5ff]/20 border border-[#00e5ff] text-[#00e5ff] hover:bg-[#00e5ff]/30 text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Wrench className="w-3.5 h-3.5" />
            Show Tools
          </button>
        </div>
      </div>

      {/* Main 2-column Layout: Detected Projects & MCP Servers */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 overflow-hidden">
        {/* Detected Projects Panel */}
        <div className="glass-panel rounded-xl p-4 flex flex-col overflow-hidden border border-[#00e5ff]/20 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#00e5ff]/20">
            <span className="text-xs font-mono font-bold text-[#d8f6ff] flex items-center gap-2">
              <Boxes className="w-4 h-4 text-[#00e5ff]" /> Detected Projects ({projects.length})
            </span>
            <span className="text-[10px] font-mono text-[#6f9bb3]">Workspace: {workspacePath}</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
            {projects.map(proj => (
              <div
                key={proj.name}
                className="p-3 rounded-lg bg-[#060e1a]/80 border border-white/5 hover:border-[#00e5ff]/40 transition-all space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#d8f6ff]">{proj.name}</span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                        proj.type === 'unity'
                          ? 'bg-[#2f6bff]/20 text-[#00e5ff] border-[#00e5ff]/40'
                          : proj.type === 'unreal'
                          ? 'bg-[#7b5cff]/20 text-[#7b5cff] border-[#7b5cff]/40'
                          : 'bg-white/10 text-[#6f9bb3] border-white/20'
                      }`}
                    >
                      {proj.type}
                    </span>
                  </div>

                  {proj.version && (
                    <span className="text-[10px] font-mono text-[#28e0a6] bg-[#28e0a6]/10 px-2 py-0.5 rounded border border-[#28e0a6]/30">
                      v{proj.version}
                    </span>
                  )}
                </div>

                <div className="text-[11px] font-mono text-[#6f9bb3] truncate">
                  Path: <code className="text-[#d8f6ff]">{proj.path}</code>
                </div>

                <div className="text-[11px] text-[#6f9bb3] flex flex-wrap gap-3 pt-1 border-t border-white/5">
                  {proj.scenes && (
                    <span>
                      Scenes: <strong className="text-[#00e5ff]">{proj.scenes.length}</strong>
                    </span>
                  )}
                  {proj.scripts && (
                    <span>
                      Scripts: <strong className="text-[#00e5ff]">{proj.scripts.length}</strong>
                    </span>
                  )}
                  {proj.modules && (
                    <span>
                      Modules: <strong className="text-[#7b5cff]">{proj.modules.length}</strong>
                    </span>
                  )}
                  <span className="ml-auto text-[10px] text-[#6f9bb3]/70">{proj.lastModified}</span>
                </div>

                <div className="pt-1 flex items-center gap-2">
                  <button
                    onClick={() => onNavigate(proj.type === 'unity' ? 'unity' : proj.type === 'unreal' ? 'unreal' : 'coding')}
                    className="text-[11px] font-mono text-[#00e5ff] hover:underline flex items-center gap-1"
                  >
                    Open in {proj.type === 'unity' ? 'Unity Tools' : proj.type === 'unreal' ? 'Unreal Tools' : 'Coding Studio'} &rarr;
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* MCP Servers Panel */}
        <div className="glass-panel rounded-xl p-4 flex flex-col overflow-hidden border border-[#00e5ff]/20 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-[#00e5ff]/20">
            <span className="text-xs font-mono font-bold text-[#d8f6ff] flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[#7b5cff]" /> MCP Server Bridges ({mcpServers.length})
            </span>
            <span className="text-[10px] font-mono text-[#28e0a6]">PROTOCOL v1.0</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
            {mcpServers.map(server => (
              <div
                key={server.name}
                className="p-3 rounded-lg bg-[#060e1a]/80 border border-white/5 hover:border-[#7b5cff]/40 transition-all space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#d8f6ff]">{server.name}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded border bg-[#28e0a6]/15 text-[#28e0a6] border-[#28e0a6]/40 flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" />
                    READY
                  </span>
                </div>

                <div className="text-[11px] font-mono text-[#6f9bb3] bg-[#04060c] p-1.5 rounded border border-white/5 truncate">
                  $ {server.command}
                </div>

                <div className="space-y-1">
                  <span className="text-[10px] text-[#6f9bb3] uppercase font-mono">Exposed Tools:</span>
                  <div className="flex flex-wrap gap-1">
                    {server.tools.map(tool => (
                      <span
                        key={tool}
                        className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-[#00e5ff] border border-[#00e5ff]/20"
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tools Modal */}
      {showToolsModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel rounded-xl max-w-lg w-full p-5 border border-[#00e5ff]/40 shadow-cyan-glow space-y-4">
            <div className="flex items-center justify-between border-b border-[#00e5ff]/20 pb-3">
              <div className="flex items-center gap-2">
                <Wrench className="w-4 h-4 text-[#00e5ff]" />
                <h3 className="text-sm font-bold text-[#d8f6ff] font-mono">Game Engine Tools & Generator</h3>
              </div>
              <button
                onClick={() => setShowToolsModal(false)}
                className="text-[#6f9bb3] hover:text-[#d8f6ff] text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <p className="text-[#6f9bb3]">
                Direct engine automation requires the Unity / Unreal editor to be active with an attached MCP socket. On-disk source inspection & C++/C# code generation are fully available.
              </p>

              <div className="p-3 rounded bg-[#060e1a] border border-[#00e5ff]/30 space-y-2">
                <div className="font-mono text-[#00e5ff] font-semibold">C++ Class Generator (Unreal):</div>
                <pre className="text-[11px] text-[#d8f6ff] font-mono bg-[#04060c] p-2 rounded overflow-x-auto">
{`UCLASS()
class NEONASCENT_API APlayerDrone : public AActor {
    GENERATED_BODY()
public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="AI")
    float ScanRadius = 1500.0f;
};`}
                </pre>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
              <button
                onClick={() => setShowToolsModal(false)}
                className="px-4 py-2 rounded-lg bg-gradient-to-r from-[#2f6bff] to-[#00e5ff] text-[#04121a] font-bold text-xs font-mono"
              >
                Close Tools
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
