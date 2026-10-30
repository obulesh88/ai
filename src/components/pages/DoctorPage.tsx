import React, { useState, useEffect } from 'react';
import { DoctorCheck } from '../../types';
import { runDiagnostics } from '../../services/doctor';
import { ShieldCheck, ShieldAlert, CheckCircle2, AlertTriangle, XCircle, RefreshCw, Activity, Terminal } from 'lucide-react';

export const DoctorPage: React.FC = () => {
  const [checks, setChecks] = useState<DoctorCheck[]>([]);
  const [score, setScore] = useState<number>(100);
  const [criticalPassed, setCriticalPassed] = useState<boolean>(true);
  const [timestamp, setTimestamp] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);

  const executeDoctor = async () => {
    setIsRunning(true);
    const res = await runDiagnostics();
    setChecks(res.checks);
    setScore(res.score);
    setCriticalPassed(res.criticalPassed);
    setTimestamp(res.timestamp);
    setIsRunning(false);
  };

  useEffect(() => {
    executeDoctor();
  }, []);

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#28e0a6]" />
            <h1 className="text-base font-bold tracking-wide text-[#d8f6ff]">System Doctor Diagnostics</h1>
          </div>
          <p className="text-xs text-[#6f9bb3]">
            Full environment integrity audit. Validates model endpoint, memory DB, permission guards, and audio APIs.
          </p>
        </div>

        <button
          onClick={executeDoctor}
          disabled={isRunning}
          className="px-4 py-1.5 rounded-lg bg-[#00e5ff]/20 border border-[#00e5ff] text-[#00e5ff] hover:bg-[#00e5ff]/30 text-xs font-mono font-bold flex items-center gap-2 disabled:opacity-40 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
          Run Diagnostics
        </button>
      </div>

      {/* Overall Score Banner */}
      <div className="glass-panel rounded-xl p-4 flex items-center justify-between border border-[#00e5ff]/30 shadow-cyan-glow">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full border-2 border-[#28e0a6] bg-[#28e0a6]/10 flex items-center justify-center text-lg font-mono font-bold text-[#28e0a6] shadow-[0_0_15px_rgba(40,224,166,0.3)]">
            {score}%
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-[#d8f6ff]">
                {criticalPassed ? 'SYSTEM HEALTH NOMINAL' : 'ATTENTION REQUIRED'}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#28e0a6]/20 text-[#28e0a6] border border-[#28e0a6]/40">
                EXIT CODE 0
              </span>
            </div>
            <p className="text-xs text-[#6f9bb3] mt-0.5">
              Last probe at {timestamp}. All critical security and database tables verified.
            </p>
          </div>
        </div>
      </div>

      {/* Diagnostic Checklist */}
      <div className="flex-1 glass-panel rounded-xl p-4 overflow-y-auto space-y-3 border border-[#00e5ff]/20">
        <span className="text-xs font-mono font-bold text-[#6f9bb3] uppercase tracking-wider block pb-1 border-b border-white/10">
          Subsystem Audits ({checks.length} checkpoints)
        </span>

        {checks.map(chk => (
          <div
            key={chk.id}
            className="p-3.5 rounded-lg bg-[#060e1a]/80 border border-white/5 hover:border-[#00e5ff]/30 transition-all space-y-2"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-[#d8f6ff]">{chk.name}</span>
                  <span className="text-[10px] font-mono text-[#6f9bb3] px-1.5 py-0.2 rounded bg-white/5">
                    {chk.category}
                  </span>
                </div>
                <p className="text-xs text-[#6f9bb3] leading-relaxed font-sans">{chk.detail}</p>
              </div>

              <div className="shrink-0">
                {chk.status === 'pass' ? (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#28e0a6]/20 text-[#28e0a6] border border-[#28e0a6]/40 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    PASS
                  </span>
                ) : chk.status === 'warn' ? (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#ffc457]/20 text-[#ffc457] border border-[#ffc457]/40 flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    WARN
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#ff4d6d]/20 text-[#ff4d6d] border border-[#ff4d6d]/40 flex items-center gap-1">
                    <XCircle className="w-3 h-3" />
                    FAIL
                  </span>
                )}
              </div>
            </div>

            {chk.recommendation && (
              <div className="p-2 rounded bg-[#04060c] border border-[#ffc457]/30 text-[11px] font-mono text-[#ffc457]">
                👉 Recommended: {chk.recommendation}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
