# HEMA - Local Personal AI Assistant (React Web Edition)

Futuristic cyberpunk personal AI assistant rewritten as a React application. Preserves all core architectural features and business logic from the original HEMA system: local model management, multi-step task planning, long-term memory with secret refusal guards, game development project inspection (Unity / Unreal), MCP bridges, Dragon Tiger probability analytics, system diagnostics, and voice controls.

## Features Ported

- **Cyberpunk Holographic Interface**: Animated HoloAvatar reacting to idle, processing, speaking, and offline states with pulsating radar rings and frequency equalizers.
- **Top Navigation Bar**: Live probe of Ollama/AI endpoint (`/api/tags`), active model selector, latency display, and voice toggle.
- **Conversation Assistant**: Streaming dialogue, command router (`plan:`, `remember:`, `doctor`, `dragon tiger`, `gamedev`, `code:`), content-sized message bubbles, code syntax formatting with clipboard copy.
- **Memory Vault**: Long-term persistent store with security guard that strictly refuses passwords, API keys, and credential secrets.
- **Tasks & Planner**: Autonomous multi-step execution graphs with status indicators (`pending`, `running`, `verified`, `completed`, `cancelled`), retry logic, and verification reports.
- **Game Development Tools**: Workspace inspection for Unity (editor version, scene hierarchy, C# scripts) and Unreal Engine (modules, .uproject files, C++ class generator) with MCP bridges.
- **Coding Studio**: Interactive code inspector, syntax optimization agent, test runner, and sandboxed console.
- **Dragon Tiger Probability Analytics**: Real card dealing simulation, statistical distributions, Big Road streak matrix, Bead Plate, and fractional Kelly bet sizing.
- **System Doctor**: Comprehensive 7-point integrity audit with real-time health score.
- **Plugins & Note Taker**: Categorized technical notes vault and active plugin manager.
- **Settings & Identity**: Custom user name and assistant name with instantaneous live updates across greeting and window title.
- **Live Telemetry HUD**: Real-time animated CPU, memory, disk, and network stream meters with live security audit logging.

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Bundler & Dev Server**: Vite
- **Styling**: Tailwind CSS with custom neon cyberpunk theme palette
- **Icons**: Lucide React
- **Audio & Speech**: Web Speech API (STT + TTS) with wake word detection

## Development

```bash
npm install
npm run dev
```

Server listens on `http://0.0.0.0:3000`.
