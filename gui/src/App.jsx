import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import MainPanel from './components/MainPanel';
import { BotProvider, useBot } from './components/BotContext';
import { Laptop, MonitorPlay, Play, Square } from 'lucide-react';

function AppContent() {
  const [activeTab, setActiveTab] = useState(1);
  const { botActive, startBot, stopBot, settings } = useBot();

  return (
    <div className="fixed inset-0 w-screen h-screen flex items-center justify-center bg-[#090d16] overflow-hidden">
      <div className="w-[1280px] h-[720px] mx-auto overflow-hidden flex bg-[#030712] text-slate-200 select-none relative font-sans border border-slate-800 rounded-xl shadow-2xl">
        
        {/* Sidebar navigation */}
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Main panel wrapper */}
        <main className="flex-1 flex flex-col h-full min-w-0">
          
          {/* Top Status bar (Header panel) */}
          <header className="h-16 border-b border-slate-800/40 glass-panel px-8 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3.5">
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900/60 border border-slate-800 rounded-full text-xs font-semibold text-slate-300">
                <Laptop className="w-3.5 h-3.5 text-cyan-400" />
                <span>Tiến trình: <span className="font-mono text-cyan-400">{settings.gameProcess}</span></span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-900/60 border border-slate-800 rounded-full text-xs font-semibold text-slate-300">
                <MonitorPlay className="w-3.5 h-3.5 text-cyan-400" />
                <span>Cửa sổ: <span className="font-mono text-cyan-400">{settings.gameWindow}</span></span>
              </div>
            </div>

            <div className="flex items-center gap-4">
              {/* Bot Control Toggle Button */}
              <button
                onClick={botActive ? stopBot : startBot}
                className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all duration-300 cursor-pointer shadow-md active:scale-95 ${
                  botActive
                    ? 'bg-rose-500/10 border border-rose-500/30 text-rose-400 hover:bg-rose-500/20 hover:border-rose-500/40'
                    : 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20 hover:border-cyan-500/40'
                }`}
              >
                {botActive ? (
                  <>
                    <Square className="w-3 h-3 fill-rose-400 text-rose-400" />
                    <span>STOP BOT ({settings.stopHotkey || 'F10'})</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3 fill-cyan-400 text-cyan-400" />
                    <span>START BOT ({settings.startHotkey || 'F9'})</span>
                  </>
                )}
              </button>

              {/* Bot Active State Badge */}
              <div className={`flex items-center gap-2 px-3 py-1 border rounded-lg text-xs font-bold tracking-wide uppercase ${
                botActive
                  ? 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400'
                  : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}>
                <span className={`w-1.5 h-1.5 rounded-full ${botActive ? 'bg-cyan-400 animate-pulse' : 'bg-slate-500'}`} />
                <span>BOT: {botActive ? 'ACTIVE' : 'STOPPED'}</span>
              </div>
            </div>
          </header>

          {/* Content panel */}
          <div className="flex-1 overflow-hidden relative">
            <MainPanel activeTab={activeTab} />
          </div>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <BotProvider>
      <AppContent />
    </BotProvider>
  );
}

export default App;
