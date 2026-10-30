import React, { useState } from 'react';
import { Terminal, Play, CheckCircle2, ShieldCheck, Bug, FileCode, RotateCcw } from 'lucide-react';

export const CodingPage: React.FC = () => {
  const [activeFile, setActiveFile] = useState('inspect_assets.py');
  const [code, setCode] = useState(`import os
from pathlib import Path

def audit_workspace_assets(root_dir: str):
    root = Path(root_dir)
    print(f"[HEMA-CODE-AGENT] Auditing: {root.resolve()}")
    results = {"unity_scenes": 0, "cpp_headers": 0, "scripts": 0}
    
    for f in root.glob("**/*"):
        if f.suffix == ".unity":
            results["unity_scenes"] += 1
        elif f.suffix in (".h", ".hpp", ".cpp"):
            results["cpp_headers"] += 1
        elif f.suffix in (".py", ".cs", ".ts"):
            results["scripts"] += 1
            
    print(f"[OK] Audit completed. Summary: {results}")
    return results

if __name__ == "__main__":
    audit_workspace_assets("./workspace")
`);

  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);

  const handleRun = () => {
    setIsRunning(true);
    setTerminalOutput([`$ python ${activeFile}`, `[HEMA-SANDBOX] Initializing isolated runtime container...`]);

    setTimeout(() => {
      setTerminalOutput(prev => [
        ...prev,
        `[HEMA-CODE-AGENT] Auditing: /app/workspace`,
        `[OK] Audit completed. Summary: {'unity_scenes': 3, 'cpp_headers': 4, 'scripts': 7}`,
        `[HEMA-SANDBOX] Process exited with code 0 (Execution time: 0.14s).`,
      ]);
      setTestResult('PASSED (1/1 tests)');
      setIsRunning(false);
    }, 900);
  };

  const handleFixCode = () => {
    setCode(prev => `# [HEMA-AGENT-OPTIMIZED]\n` + prev + `\n# Safe error-handling wrapper attached\n`);
    setTerminalOutput([`[HEMA-AGENT] Attached security boundary check & type annotations.`]);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div>
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-[#00e5ff]" />
            <h1 className="text-base font-bold tracking-wide text-[#d8f6ff]">Coding Studio & Agent</h1>
          </div>
          <p className="text-xs text-[#6f9bb3]">
            Autonomous code generation, test runner, syntax inspector, and secure workspace sandbox execution.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleFixCode}
            className="px-3 py-1.5 rounded-lg border border-[#7b5cff]/40 text-[#7b5cff] hover:bg-[#7b5cff]/10 text-xs font-mono flex items-center gap-1.5 transition-colors"
          >
            <Bug className="w-3.5 h-3.5" />
            Auto-Fix & Optimize
          </button>

          <button
            onClick={handleRun}
            disabled={isRunning}
            className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-[#2f6bff] to-[#00e5ff] text-[#04121a] font-bold text-xs font-mono flex items-center gap-1.5 shadow-[0_0_12px_rgba(0,229,255,0.3)] hover:opacity-90 disabled:opacity-40"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {isRunning ? 'Running...' : 'Run Code'}
          </button>
        </div>
      </div>

      {/* Editor & Terminal 2-panel layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden">
        {/* Code Editor (7 cols) */}
        <div className="lg:col-span-7 glass-panel rounded-xl p-3 flex flex-col overflow-hidden border border-[#00e5ff]/20 space-y-2">
          {/* File tabs */}
          <div className="flex items-center justify-between pb-2 border-b border-white/10 text-xs font-mono">
            <div className="flex items-center gap-2">
              {['inspect_assets.py', 'cli.py', 'stats_parser.py'].map(f => (
                <button
                  key={f}
                  onClick={() => setActiveFile(f)}
                  className={`px-2.5 py-1 rounded text-[11px] flex items-center gap-1.5 ${
                    activeFile === f
                      ? 'bg-[#00e5ff]/20 text-[#00e5ff] border border-[#00e5ff]/40 font-bold'
                      : 'text-[#6f9bb3] hover:text-[#d8f6ff]'
                  }`}
                >
                  <FileCode className="w-3 h-3" />
                  {f}
                </button>
              ))}
            </div>

            <span className="text-[10px] text-[#28e0a6] flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              Workspace Guarded
            </span>
          </div>

          <textarea
            value={code}
            onChange={e => setCode(e.target.value)}
            spellCheck={false}
            className="flex-1 bg-[#04060c] border border-white/5 focus:border-[#00e5ff]/40 rounded-lg p-3 text-xs text-[#d8f6ff] font-mono leading-relaxed resize-none focus:outline-none"
          />
        </div>

        {/* Sandbox Output & Test Runner (5 cols) */}
        <div className="lg:col-span-5 glass-panel rounded-xl p-3 flex flex-col overflow-hidden border border-[#00e5ff]/20 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-white/10 text-xs font-mono">
            <span className="text-[#00e5ff] font-bold flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5" /> Execution Console
            </span>
            {testResult && (
              <span className="text-[10px] px-2 py-0.5 rounded bg-[#28e0a6]/20 text-[#28e0a6] border border-[#28e0a6]/40 font-bold">
                {testResult}
              </span>
            )}
          </div>

          <div className="flex-1 bg-[#04060c] border border-white/5 rounded-lg p-3 font-mono text-[11px] overflow-y-auto space-y-1">
            {terminalOutput.length === 0 ? (
              <p className="text-[#6f9bb3]/60 italic">Click "Run Code" to execute script in the safe sandbox environment.</p>
            ) : (
              terminalOutput.map((line, idx) => (
                <div
                  key={idx}
                  className={
                    line.includes('[OK]') || line.includes('PASSED')
                      ? 'text-[#28e0a6]'
                      : line.includes('$')
                      ? 'text-[#00e5ff]'
                      : 'text-[#d8f6ff]'
                  }
                >
                  {line}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
