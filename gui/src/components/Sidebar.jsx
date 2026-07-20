import React from 'react';
import { 
  Play, 
  Settings, 
  Zap, 
  ListMusic, 
  Activity 
} from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const menuItems = [
    {
      id: 1,
      title: 'Chức năng 1',
      subtitle: 'Điều khiển Bot (F9/F10)',
      icon: Play,
    },
    {
      id: 2,
      title: 'Chức năng 2',
      subtitle: 'Cài đặt Phím & Game',
      icon: Settings,
    },
    {
      id: 3,
      title: 'Chức năng 3',
      subtitle: 'Thực thi Combo nhanh',
      icon: Zap,
    },
    {
      id: 4,
      title: 'Chức năng 4',
      subtitle: 'Vòng lặp Playlist',
      icon: ListMusic,
    },
    {
      id: 5,
      title: 'Chức năng 5',
      subtitle: 'Trạng thái & Tiến trình',
      icon: Activity,
    },
  ];

  return (
    <aside className="w-80 glass-panel border-r border-slate-800/60 p-6 flex flex-col justify-between shrink-0 h-full">
      <div className="flex flex-col gap-8">
        {/* Header/Logo section */}
        <div className="flex items-center gap-3 px-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <span className="font-bold text-white text-lg tracking-wider">Ω</span>
          </div>
          <div>
            <h1 className="font-black text-xl tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
              AUTO BOT
            </h1>
            <p className="text-[10px] text-cyan-400 font-bold tracking-widest uppercase">
              FIGHTING ENGINE
            </p>
          </div>
        </div>

        {/* Navigation list */}
        <nav className="flex flex-col gap-3">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-4 px-4 py-3.5 rounded-xl text-left transition-all duration-300 group relative ${
                  isActive
                    ? 'bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.1)]'
                    : 'bg-transparent border border-transparent text-slate-400 hover:bg-slate-800/30 hover:border-slate-800 hover:text-slate-200'
                }`}
              >
                {/* Active indicator bar */}
                {isActive && (
                  <div className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-cyan-400 rounded-r-md" />
                )}

                <div className={`p-2 rounded-lg transition-colors duration-300 ${
                  isActive ? 'bg-cyan-500/20 text-cyan-300' : 'bg-slate-800/40 text-slate-500 group-hover:text-slate-300'
                }`}>
                  <Icon className="w-5 h-5" />
                </div>

                <div className="flex flex-col">
                  <span className={`font-semibold text-sm tracking-wide transition-colors ${
                    isActive ? 'text-cyan-400 cyan-neon-glow' : 'text-slate-300'
                  }`}>
                    {item.title}
                  </span>
                  <span className="text-[11px] text-slate-500 group-hover:text-slate-400 mt-0.5 font-medium transition-colors">
                    {item.subtitle}
                  </span>
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Footer information */}
      <div className="mt-8 pt-6 border-t border-slate-800/50 px-2 flex items-center justify-between text-xs text-slate-500 font-medium">
        <span>Phiên bản v0.101</span>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-emerald-400">Backend Connected</span>
        </div>
      </div>
    </aside>
  );
};

export default React.memo(Sidebar);
