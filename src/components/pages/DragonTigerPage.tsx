import React, { useState, useMemo } from 'react';
import { DragonTigerRound } from '../../types';
import {
  computeStats,
  generateInitialShoe,
  playRound,
} from '../../services/dragonTiger';
import { TrendingUp, Play, RotateCcw, Sparkles, Award, AlertCircle } from 'lucide-react';

export const DragonTigerPage: React.FC = () => {
  const [rounds, setRounds] = useState<DragonTigerRound[]>(() => generateInitialShoe());
  const [lastDealt, setLastDealt] = useState<DragonTigerRound | null>(() => rounds[rounds.length - 1] || null);

  const stats = useMemo(() => computeStats(rounds), [rounds]);

  const handleDealOne = () => {
    const nextId = rounds.length ? Math.max(...rounds.map(r => r.id)) + 1 : 1;
    const r = playRound(nextId);
    setRounds(prev => [...prev, r]);
    setLastDealt(r);
  };

  const handleSimulateTen = () => {
    const newBatch: DragonTigerRound[] = [];
    let currentId = rounds.length ? Math.max(...rounds.map(r => r.id)) + 1 : 1;
    for (let i = 0; i < 10; i++) {
      newBatch.push(playRound(currentId++));
    }
    setRounds(prev => [...prev, ...newBatch]);
    setLastDealt(newBatch[newBatch.length - 1]);
  };

  const handleResetShoe = () => {
    const initial = generateInitialShoe();
    setRounds(initial);
    setLastDealt(initial[initial.length - 1]);
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-4 space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border border-[#00e5ff]/20">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[#ff4d6d]" />
            <h1 className="text-base font-bold tracking-wide text-[#d8f6ff]">
              Dragon Tiger Probability Analytics
            </h1>
          </div>
          <p className="text-xs text-[#6f9bb3]">
            Mathematical shoe modeling, Big Road matrices, streak clustering, and fractional Kelly bet recommendations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSimulateTen}
            className="px-3 py-1.5 rounded-lg border border-[#00e5ff]/30 text-[#00e5ff] hover:bg-[#00e5ff]/10 text-xs font-mono transition-colors"
          >
            +10 Rounds
          </button>
          <button
            onClick={handleDealOne}
            className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-[#2f6bff] to-[#00e5ff] text-[#04121a] font-bold text-xs font-mono shadow-[0_0_12px_rgba(0,229,255,0.4)] flex items-center gap-1.5 hover:opacity-90 transition-opacity"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            Deal Hand
          </button>
          <button
            onClick={handleResetShoe}
            className="p-1.5 rounded-lg border border-white/10 text-[#6f9bb3] hover:text-[#d8f6ff]"
            title="Reset Shoe"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Top Stats Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {/* Dragon Card */}
        <div className="glass-panel rounded-xl p-3 border border-[#ff4d6d]/30 bg-[#ff4d6d]/5 space-y-1">
          <span className="text-[10px] font-mono uppercase text-[#ff4d6d] font-bold">DRAGON WINS</span>
          <div className="text-xl font-mono font-bold text-[#d8f6ff]">{stats.dragonWins}</div>
          <div className="text-[11px] font-mono text-[#6f9bb3]">{stats.dragonPct}% of shoe</div>
        </div>

        {/* Tiger Card */}
        <div className="glass-panel rounded-xl p-3 border border-[#2f6bff]/30 bg-[#2f6bff]/5 space-y-1">
          <span className="text-[10px] font-mono uppercase text-[#00e5ff] font-bold">TIGER WINS</span>
          <div className="text-xl font-mono font-bold text-[#d8f6ff]">{stats.tigerWins}</div>
          <div className="text-[11px] font-mono text-[#6f9bb3]">{stats.tigerPct}% of shoe</div>
        </div>

        {/* Tie Card */}
        <div className="glass-panel rounded-xl p-3 border border-[#28e0a6]/30 bg-[#28e0a6]/5 space-y-1">
          <span className="text-[10px] font-mono uppercase text-[#28e0a6] font-bold">TIES (8:1)</span>
          <div className="text-xl font-mono font-bold text-[#d8f6ff]">{stats.ties}</div>
          <div className="text-[11px] font-mono text-[#6f9bb3]">{stats.tiePct}% of shoe</div>
        </div>

        {/* Current Streak */}
        <div className="glass-panel rounded-xl p-3 border border-[#ffc457]/30 bg-[#ffc457]/5 space-y-1">
          <span className="text-[10px] font-mono uppercase text-[#ffc457] font-bold">CURRENT STREAK</span>
          <div className="text-xl font-mono font-bold text-[#ffc457] uppercase">
            {stats.currentStreak.count}x {stats.currentStreak.winner}
          </div>
          <div className="text-[11px] font-mono text-[#6f9bb3]">Max D:{stats.longestStreak.dragon} | T:{stats.longestStreak.tiger}</div>
        </div>

        {/* Recommendation */}
        <div className="glass-panel rounded-xl p-3 border border-[#7b5cff]/40 bg-[#7b5cff]/10 space-y-1 col-span-2 md:col-span-1">
          <span className="text-[10px] font-mono uppercase text-[#7b5cff] font-bold flex items-center gap-1">
            <Sparkles className="w-3 h-3" /> MODEL CALL
          </span>
          <div className="text-xl font-mono font-bold text-[#00e5ff] uppercase">
            {stats.prediction.recommended}
          </div>
          <div className="text-[11px] font-mono text-[#28e0a6]">{stats.prediction.confidence}% confidence</div>
        </div>
      </div>

      {/* Main Analysis Section: Live Card Deal & Roadmaps */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden">
        {/* Deal Table & Prediction Callout (5 cols) */}
        <div className="lg:col-span-5 glass-panel rounded-xl p-4 flex flex-col justify-between overflow-y-auto border border-[#00e5ff]/20 space-y-4">
          <div>
            <span className="text-xs font-mono font-bold text-[#6f9bb3] uppercase block mb-3">
              Last Dealt Hand (#{lastDealt?.id || 0})
            </span>

            {lastDealt ? (
              <div className="flex items-center justify-around p-4 rounded-xl bg-[#060e1a] border border-[#00e5ff]/30">
                {/* Dragon Card */}
                <div className="flex flex-col items-center space-y-1.5">
                  <span className="text-xs font-mono font-bold text-[#ff4d6d]">DRAGON</span>
                  <div className="w-16 h-24 rounded-lg bg-white text-slate-900 border-2 border-[#ff4d6d] shadow-[0_0_15px_rgba(255,77,109,0.3)] flex flex-col items-center justify-center font-bold text-lg select-none">
                    <span className={lastDealt.dragonCard.suit === '♥' || lastDealt.dragonCard.suit === '♦' ? 'text-red-600' : 'text-black'}>
                      {lastDealt.dragonCard.rank}
                    </span>
                    <span className="text-xl">
                      {lastDealt.dragonCard.suit}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-[#6f9bb3]">Score: {lastDealt.dragonCard.value}</span>
                </div>

                <div className="text-center font-mono font-bold">
                  <span className="text-xs text-[#6f9bb3] block">VS</span>
                  <span
                    className={`text-sm px-2.5 py-0.5 rounded uppercase mt-2 inline-block ${
                      lastDealt.winner === 'dragon'
                        ? 'bg-[#ff4d6d]/20 text-[#ff4d6d]'
                        : lastDealt.winner === 'tiger'
                        ? 'bg-[#00e5ff]/20 text-[#00e5ff]'
                        : 'bg-[#28e0a6]/20 text-[#28e0a6]'
                    }`}
                  >
                    {lastDealt.winner} WIN
                  </span>
                </div>

                {/* Tiger Card */}
                <div className="flex flex-col items-center space-y-1.5">
                  <span className="text-xs font-mono font-bold text-[#00e5ff]">TIGER</span>
                  <div className="w-16 h-24 rounded-lg bg-white text-slate-900 border-2 border-[#00e5ff] shadow-[0_0_15px_rgba(0,229,255,0.3)] flex flex-col items-center justify-center font-bold text-lg select-none">
                    <span className={lastDealt.tigerCard.suit === '♥' || lastDealt.tigerCard.suit === '♦' ? 'text-red-600' : 'text-black'}>
                      {lastDealt.tigerCard.rank}
                    </span>
                    <span className="text-xl">
                      {lastDealt.tigerCard.suit}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-[#6f9bb3]">Score: {lastDealt.tigerCard.value}</span>
                </div>
              </div>
            ) : null}
          </div>

          {/* Sizing & Model Logic */}
          <div className="p-3.5 rounded-lg bg-[#060e1a] border border-[#7b5cff]/30 space-y-2 text-xs font-mono">
            <div className="flex items-center gap-2 text-[#7b5cff] font-bold">
              <Award className="w-4 h-4" />
              <span>Statistical Inference</span>
            </div>
            <p className="text-[#d8f6ff] leading-relaxed text-[11px] font-sans">
              {stats.prediction.reasoning}
            </p>
            <div className="pt-2 border-t border-white/10 flex items-center justify-between text-[11px]">
              <span className="text-[#6f9bb3]">Kelly Fraction (1/4):</span>
              <span className="text-[#28e0a6] font-bold">
                {(stats.prediction.kellyFraction * 100).toFixed(2)}% of Bankroll
              </span>
            </div>
          </div>
        </div>

        {/* Big Road & Bead Plate Roadmap (7 cols) */}
        <div className="lg:col-span-7 glass-panel rounded-xl p-4 flex flex-col overflow-hidden border border-[#00e5ff]/20 space-y-4">
          {/* Big Road Grid */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-[#d8f6ff] uppercase">
                Big Road Matrix (Streak Columns)
              </span>
              <span className="text-[10px] font-mono text-[#6f9bb3]">
                Red = Dragon, Blue = Tiger, Green = Tie
              </span>
            </div>

            <div className="h-40 bg-[#04060c] p-2 rounded-lg border border-white/10 overflow-x-auto flex gap-1.5 items-start">
              {stats.bigRoad.map((col, colIdx) => (
                <div key={colIdx} className="flex flex-col gap-1.5 shrink-0">
                  {col.map((cell, cellIdx) => (
                    <div
                      key={cellIdx}
                      className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold font-mono border ${
                        cell.winner === 'dragon'
                          ? 'border-[#ff4d6d] text-[#ff4d6d] bg-[#ff4d6d]/20'
                          : cell.winner === 'tiger'
                          ? 'border-[#00e5ff] text-[#00e5ff] bg-[#00e5ff]/20'
                          : 'border-[#28e0a6] text-[#28e0a6] bg-[#28e0a6]/20'
                      }`}
                      title={`${cell.winner.toUpperCase()}${cell.tiesCount > 0 ? ` (+${cell.tiesCount} Ties)` : ''}`}
                    >
                      {cell.winner[0].toUpperCase()}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Bead Plate Sequential History */}
          <div className="space-y-2 flex-1 overflow-hidden flex flex-col">
            <span className="text-xs font-mono font-bold text-[#d8f6ff] uppercase">
              Sequential Bead Plate ({rounds.length} hands)
            </span>
            <div className="flex-1 bg-[#04060c] p-2 rounded-lg border border-white/10 overflow-y-auto flex flex-wrap gap-1 content-start">
              {rounds.map(r => (
                <div
                  key={r.id}
                  className={`w-6 h-6 rounded text-[10px] font-mono font-bold flex items-center justify-center select-none ${
                    r.winner === 'dragon'
                      ? 'bg-[#ff4d6d]/20 text-[#ff4d6d] border border-[#ff4d6d]/50'
                      : r.winner === 'tiger'
                      ? 'bg-[#00e5ff]/20 text-[#00e5ff] border border-[#00e5ff]/50'
                      : 'bg-[#28e0a6]/20 text-[#28e0a6] border border-[#28e0a6]/50'
                  }`}
                  title={`Round #${r.id}: ${r.winner.toUpperCase()} (${r.dragonCard.rank}${r.dragonCard.suit} vs ${r.tigerCard.rank}${r.tigerCard.suit})`}
                >
                  {r.winner[0].toUpperCase()}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
