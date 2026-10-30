import React, { useState } from 'react';
import { ProjectInfo } from '../../types';
import { Layers, CheckCircle, Code2, Play, Wrench, Shield } from 'lucide-react';

interface UnrealPageProps {
  projects: ProjectInfo[];
  workspacePath: string;
}

export const UnrealPage: React.FC<UnrealPageProps> = ({ projects, workspacePath }) => {
  const unrealProjects = projects.filter(p => p.type === 'unreal');
  const [activeProj, setActiveProj] = useState(unrealProjects[0] || null);
  const [generatedSnippet, setGeneratedSnippet] = useState<string | null>(null);

  const handleGenerateClass = () => {
    setGeneratedSnippet(`// Source/NeonAscentCore/Public/CyberCharacter.h
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "CyberCharacter.generated.h"

UCLASS(BlueprintType, Blueprintable)
class NEONASCENTCORE_API ACyberCharacter : public ACharacter {
    GENERATED_BODY()

public:
    ACyberCharacter();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cybernetics")
    float OverclockRatio = 1.45f;

    UFUNCTION(BlueprintCallable, Category="Cybernetics")
    void TriggerNeuralSurge();
};`);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#7b5cff]" />
            <h1 className="text-base font-bold tracking-wide text-[#d8f6ff]">Unreal Engine Tools</h1>
          </div>
          <p className="text-xs text-[#6f9bb3]">
            C++ classes can be generated on disk; builds and editor actions require your explicit approval.
          </p>
        </div>

        <button
          onClick={handleGenerateClass}
          className="px-3.5 py-1.5 rounded-lg bg-[#7b5cff]/20 border border-[#7b5cff] text-[#7b5cff] hover:bg-[#7b5cff]/30 text-xs font-mono font-semibold flex items-center gap-1.5 transition-colors"
        >
          <Code2 className="w-3.5 h-3.5" />
          Generate C++ Class
        </button>
      </div>

      {unrealProjects.length === 0 ? (
        <div className="flex-1 glass-panel rounded-xl p-8 flex flex-col items-center justify-center text-center text-[#6f9bb3]">
          <Layers className="w-12 h-12 text-[#7b5cff]/40 mb-3" />
          <h3 className="text-sm font-semibold text-[#d8f6ff]">No Unreal Engine project found in {workspacePath}</h3>
          <p className="text-xs max-w-sm mt-1">
            Place an Unreal .uproject folder inside {workspacePath} to enable module and build inspection.
          </p>
        </div>
      ) : (
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden">
          {/* Project List (4 cols) */}
          <div className="lg:col-span-4 glass-panel rounded-xl p-4 flex flex-col overflow-hidden border border-[#00e5ff]/20 space-y-3">
            <span className="text-xs font-mono font-bold text-[#6f9bb3] uppercase">
              Unreal Projects ({unrealProjects.length})
            </span>

            <div className="space-y-2 overflow-y-auto flex-1">
              {unrealProjects.map(p => (
                <div
                  key={p.name}
                  onClick={() => setActiveProj(p)}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    activeProj?.name === p.name
                      ? 'bg-[#7b5cff]/15 border-[#7b5cff] shadow-[0_0_12px_rgba(123,92,255,0.2)]'
                      : 'bg-[#060e1a]/80 border-white/5 hover:border-[#7b5cff]/30'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#d8f6ff]">{p.name}</span>
                    <span className="text-[10px] font-mono text-[#7b5cff]">UE {p.version}</span>
                  </div>
                  <div className="text-[11px] font-mono text-[#6f9bb3] truncate mt-1">
                    {p.path}
                  </div>
                </div>
              ))}
            </div>

            <div className="p-2.5 rounded bg-[#060e1a] border border-white/5 text-[11px] text-[#6f9bb3] leading-relaxed">
              💡 1 Unreal project inspected from disk. Generating C++ classes and running approved build commands through command runner is supported; Blueprint editing is not simulated.
            </div>
          </div>

          {/* Project Details (8 cols) */}
          <div className="lg:col-span-8 glass-panel rounded-xl p-4 flex flex-col overflow-y-auto border border-[#00e5ff]/20 space-y-4">
            {activeProj && (
              <>
                <div className="flex items-center justify-between pb-3 border-b border-[#00e5ff]/20">
                  <div>
                    <h2 className="text-sm font-bold text-[#7b5cff] font-mono">{activeProj.name}</h2>
                    <span className="text-xs text-[#6f9bb3]">Engine Version: Unreal Engine {activeProj.version}</span>
                  </div>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#28e0a6]/20 text-[#28e0a6] border border-[#28e0a6]/40 flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5" />
                    Inspected .uproject
                  </span>
                </div>

                {/* Modules */}
                <div className="space-y-2">
                  <span className="text-xs font-mono font-bold text-[#d8f6ff] flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-[#7b5cff]" /> C++ Target Modules ({activeProj.modules?.length || 0})
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {activeProj.modules?.map(m => (
                      <div key={m} className="p-2.5 rounded bg-[#060e1a] border border-white/5 text-xs font-mono text-[#d8f6ff] flex items-center justify-between">
                        <span>{m}</span>
                        <span className="text-[10px] text-[#7b5cff]">Module Loaded</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Generated C++ Snippet if created */}
                {generatedSnippet && (
                  <div className="space-y-2 p-3 rounded bg-[#060e1a] border border-[#7b5cff]/40">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono text-[#7b5cff] font-bold">Generated C++ Header:</span>
                      <span className="text-[10px] text-[#28e0a6]">Safe Workspace Output</span>
                    </div>
                    <pre className="text-[11px] font-mono text-[#d8f6ff] bg-[#04060c] p-2.5 rounded overflow-x-auto leading-relaxed border border-white/5">
                      {generatedSnippet}
                    </pre>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
