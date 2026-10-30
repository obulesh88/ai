import React, { useEffect, useState } from 'react';

interface HoloAvatarProps {
  state: 'idle' | 'processing' | 'offline' | 'speaking';
  size?: number;
  interactive?: boolean;
  onClick?: () => void;
}

export const HoloAvatar: React.FC<HoloAvatarProps> = ({
  state = 'idle',
  size = 180,
  interactive = true,
  onClick,
}) => {
  const [pulse, setPulse] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPulse(p => (p + 1) % 360);
    }, 40);
    return () => clearInterval(interval);
  }, []);

  const isBusy = state === 'processing';
  const isSpeaking = state === 'speaking';
  const isOffline = state === 'offline';

  // Dynamic colors based on state
  const primaryGlow = isOffline
    ? '#ffc457'
    : isBusy
    ? '#00e5ff'
    : isSpeaking
    ? '#7b5cff'
    : '#00e5ff';
  const secondaryColor = isOffline ? '#ff4d6d' : '#2f6bff';

  return (
    <div
      onClick={interactive ? onClick : undefined}
      className={`relative flex items-center justify-center select-none ${
        interactive ? 'cursor-pointer group' : ''
      }`}
      style={{ width: size, height: size }}
      title={`HEMA Avatar (${state.toUpperCase()})`}
    >
      {/* Outer ambient glow field */}
      <div
        className="absolute inset-0 rounded-full blur-2xl opacity-40 transition-all duration-700 pointer-events-none"
        style={{
          backgroundColor: primaryGlow,
          transform: isBusy ? 'scale(1.2)' : 'scale(0.95)',
        }}
      />

      {/* Outer segmented radar ring */}
      <svg
        className={`absolute inset-0 w-full h-full pointer-events-none ${
          isBusy ? 'animate-spin' : isSpeaking ? 'animate-spin-slow' : 'animate-spin-reverse'
        }`}
        viewBox="0 0 100 100"
      >
        <circle
          cx="50"
          cy="50"
          r="46"
          fill="none"
          stroke={primaryGlow}
          strokeWidth="1.2"
          strokeDasharray="4 6 12 8 2 10"
          opacity={isOffline ? 0.3 : 0.65}
        />
        <circle
          cx="50"
          cy="50"
          r="41"
          fill="none"
          stroke={secondaryColor}
          strokeWidth="0.8"
          strokeDasharray="2 12"
          opacity="0.5"
        />
      </svg>

      {/* Middle rotating hex tech ring */}
      <svg
        className={`absolute inset-0 w-full h-full pointer-events-none ${
          isBusy ? 'animate-spin-reverse' : 'animate-spin-slow'
        }`}
        viewBox="0 0 100 100"
      >
        <polygon
          points="50,12 83,31 83,69 50,88 17,69 17,31"
          fill="none"
          stroke={primaryGlow}
          strokeWidth="1"
          opacity="0.55"
          strokeDasharray="6 8"
        />
        {/* Cardinal tick markers */}
        <line x1="50" y1="4" x2="50" y2="10" stroke={primaryGlow} strokeWidth="1.5" />
        <line x1="50" y1="90" x2="50" y2="96" stroke={primaryGlow} strokeWidth="1.5" />
        <line x1="4" y1="50" x2="10" y2="50" stroke={primaryGlow} strokeWidth="1.5" />
        <line x1="90" y1="50" x2="96" y2="50" stroke={primaryGlow} strokeWidth="1.5" />
      </svg>

      {/* Equalizer frequency bars when speaking */}
      {isSpeaking && (
        <div className="absolute inset-0 flex items-center justify-around px-8 pointer-events-none">
          {[40, 75, 95, 60, 85, 50, 70].map((h, i) => (
            <div
              key={i}
              className="w-1 bg-[#00e5ff] rounded-full transition-all duration-150"
              style={{
                height: `${Math.sin((pulse * 8 + i * 45) * (Math.PI / 180)) * 25 + 30}px`,
                opacity: 0.8,
              }}
            />
          ))}
        </div>
      )}

      {/* Inner Glowing Core */}
      <div
        className={`relative z-10 rounded-full flex items-center justify-center transition-all duration-300 ${
          interactive ? 'group-hover:scale-105' : ''
        }`}
        style={{
          width: size * 0.45,
          height: size * 0.45,
          background: `radial-gradient(circle at 35% 35%, ${primaryGlow} 0%, ${secondaryColor} 65%, #04060c 100%)`,
          boxShadow: `0 0 25px ${primaryGlow}`,
        }}
      >
        {/* Hologram Core Symbol */}
        <div className="w-6 h-6 border-2 border-white/80 rounded-sm rotate-45 flex items-center justify-center shadow-lg">
          <div
            className="w-2.5 h-2.5 bg-white rounded-full animate-ping"
            style={{ animationDuration: isBusy ? '0.8s' : '2.5s' }}
          />
        </div>
      </div>

      {/* Status Pill Badge at bottom */}
      <div className="absolute -bottom-1 z-20 px-2.5 py-0.5 rounded-full text-[10px] font-mono tracking-widest uppercase border bg-[#0a1220]/95 backdrop-blur-md shadow-md flex items-center gap-1.5"
        style={{
          borderColor: primaryGlow,
          color: primaryGlow,
        }}
      >
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{
            backgroundColor: primaryGlow,
            boxShadow: `0 0 6px ${primaryGlow}`,
          }}
        />
        {state}
      </div>
    </div>
  );
};
