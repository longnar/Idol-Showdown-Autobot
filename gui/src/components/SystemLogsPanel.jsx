import React from 'react';
import { useBot } from './BotContext';
import { Cpu, Activity, RefreshCw, AlertTriangle, ShieldAlert, CheckCircle } from 'lucide-react';

const SystemLogsPanel = () => {
  const { logs, settings, addLog } = useBot();

  const handleRefreshDiagnostics = () => {
    addLog('info', 'Refreshing process statistics and memory metrics...');
  };

  return (
    <div className="flex-1 flex flex-col justify-between p-6 scanline-bg relative h-full overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/4 right-1/4 w-96 h-96 rounded-full bg-cyan-500/5 blur-[120px] pointer-events-none pulse-glow-circle" />

      <div className="max-w-4xl w-full mx-auto flex-1 flex flex-col gap-4 overflow-hidden">
        
        {/* Title */}
        <div className="flex items-center justify-between gap-4 shrink-0">
          <div>
            <div className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5" /> SYSTEM MONITOR
            </div>
            <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              Trạng thái & Tiến trình (Logs)
            </h2>
            <p className="text-slate-400 text-xs mt-1">
              Theo dõi và chẩn đoán kết nối của bot với cửa sổ trò chơi theo thời gian thực.
            </p>
          </div>

          <button
            onClick={handleRefreshDiagnostics}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-900 border border-slate-800 text-cyan-400 hover:text-cyan-300 hover:bg-slate-850 hover:border-slate-700 text-xs font-bold transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            LÀM MỚI CHẨN ĐOÁN
          </button>
        </div>

        {/* Diagnostics Metrics Card */}
        <div className="grid grid-cols-3 gap-4 mt-2 shrink-0">
          
          <div className="glass-panel rounded-xl p-4 border border-slate-800/40">
            <span className="text-[10px] text-slate-500 font-bold block uppercase">Attached Process</span>
            <span className="text-sm font-mono font-bold text-white mt-1 block truncate">
              {settings.gameProcess}
            </span>
          </div>

          <div className="glass-panel rounded-xl p-4 border border-slate-800/40">
            <span className="text-[10px] text-slate-500 font-bold block uppercase">Memory Footprint</span>
            <span className="text-sm font-mono font-bold text-cyan-400 mt-1 block">
              42.8 MB
            </span>
          </div>

          <div className="glass-panel rounded-xl p-4 border border-slate-800/40">
            <span className="text-[10px] text-slate-500 font-bold block uppercase">Running Threads</span>
            <span className="text-sm font-mono font-bold text-emerald-400 mt-1 block">
              3 active
            </span>
          </div>
        </div>

        {/* Interactive Logs Output Screen */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col flex-1 overflow-hidden transition-all duration-300 hover:border-slate-700/50">
          <h3 className="text-xs font-bold text-cyan-400 mb-3 border-b border-slate-800 pb-2 tracking-wider flex items-center gap-2 shrink-0">
            <Cpu className="w-4 h-4 text-cyan-500" />
            LOG CONSOLE OUTPUT (REAL-TIME)
          </h3>

          <div className="flex-1 overflow-y-auto flex flex-col gap-2 font-mono text-[11px] pr-2">
            {logs.map((log, index) => {
              let colorClass = 'text-cyan-500/80';
              let Icon = Cpu;
              if (log.type === 'success') {
                colorClass = 'text-emerald-400';
                Icon = CheckCircle;
              } else if (log.type === 'warning') {
                colorClass = 'text-amber-400';
                Icon = AlertTriangle;
              } else if (log.type === 'error') {
                colorClass = 'text-rose-400';
                Icon = ShieldAlert;
              }
              
              return (
                <div key={index} className={`flex items-start gap-2.5 py-1 px-2.5 rounded hover:bg-slate-900/40 ${colorClass}`}>
                  <span className="text-[10px] text-slate-600 select-none shrink-0 mt-0.5">[{log.timestamp}]</span>
                  <span className="shrink-0 mt-0.5"><Icon className="w-3.5 h-3.5" /></span>
                  <span className="leading-relaxed">{log.msg}</span>
                </div>
              );
            })}
          </div>
        </div>

      </div>

      {/* Spacing footer */}
      <div className="h-2 shrink-0" />
    </div>
  );
};

export default SystemLogsPanel;
