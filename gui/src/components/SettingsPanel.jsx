import React, { useState, useEffect } from 'react';
import { useBot } from './BotContext';
import { Play, Pause, Clock, Save, Cpu, CheckCircle, Info, Keyboard } from 'lucide-react';

const SettingsPanel = () => {
  const { settings, saveGeneralSettings, playlists } = useBot();

  // Local state for settings form
  const [delayFrames, setDelayFrames] = useState(settings.delayFrames);
  const [isPlayer2Right, setIsPlayer2Right] = useState(settings.isPlayer2Right);
  const [selectedComboSet, setSelectedComboSet] = useState(settings.selectedComboSet);
  const [startHotkey, setStartHotkey] = useState(settings.startHotkey);
  const [stopHotkey, setStopHotkey] = useState(settings.stopHotkey);

  // States for capturing hotkeys
  const [listeningFor, setListeningFor] = useState(null); // 'start' | 'stop' | null
  const [saveStatus, setSaveStatus] = useState(null);

  // Synchronize local state with context when settings load
  useEffect(() => {
    setDelayFrames(settings.delayFrames);
    setIsPlayer2Right(settings.isPlayer2Right);
    setSelectedComboSet(settings.selectedComboSet);
    setStartHotkey(settings.startHotkey);
    setStopHotkey(settings.stopHotkey);
  }, [settings]);

  // Capture hotkey keypress
  useEffect(() => {
    if (!listeningFor) return;

    const handleKeyDown = (e) => {
      e.preventDefault();
      e.stopPropagation();

      let keyName = e.key;
      // Convert to uppercase for hotkey presentation (e.g. F9, F10, A, S)
      if (keyName.length === 1) {
        keyName = keyName.toUpperCase();
      } else if (keyName.startsWith('Arrow')) {
        keyName = keyName.replace('Arrow', '').toUpperCase();
      }

      if (listeningFor === 'start') {
        setStartHotkey(keyName);
      } else if (listeningFor === 'stop') {
        setStopHotkey(keyName);
      }
      setListeningFor(null);
    };

    window.addEventListener('keydown', handleKeyDown, true);
    return () => {
      window.removeEventListener('keydown', handleKeyDown, true);
    };
  }, [listeningFor]);

  const handleSave = async () => {
    setSaveStatus('saving');
    const success = await saveGeneralSettings({
      delayFrames,
      isPlayer2Right,
      selectedComboSet,
      startHotkey,
      stopHotkey
    });

    if (success) {
      setSaveStatus('success');
      setTimeout(() => setSaveStatus(null), 3000);
    } else {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  return (
    <div className="flex-1 flex flex-col justify-between p-6 scanline-bg relative h-full overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute top-1/4 right-1/4 w-96 h-96 rounded-full bg-cyan-500/5 blur-[120px] pointer-events-none pulse-glow-circle" />
      
      <div className="flex-1 overflow-y-auto max-w-4xl w-full mx-auto flex flex-col gap-5 pr-2">
        
        {/* Title Section */}
        <div>
          <div className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5" /> THIẾT LẬP CHUNG
          </div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight">
            Cấu hình Bot & Trạng thái Game
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Quản lý phím tắt kích hoạt bot, độ trễ hành động và cấu hình bên chơi của Player 2.
          </p>
        </div>

        {/* Game Status Panel */}
        <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all duration-300 hover:border-slate-700/50">
          <div>
            <h3 className="text-sm font-bold text-slate-200 mb-1 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Game Status: ACTIVE
            </h3>
            <p className="text-xs text-slate-400">
              Bot đã kết nối với tiến trình <span className="font-mono text-cyan-400">{settings.gameProcess}</span> và sẵn sàng thực thi.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold rounded-lg tracking-wider uppercase">
              Connected
            </span>
            <span className="px-3 py-1.5 bg-slate-900 border border-slate-800 text-slate-300 text-xs font-mono rounded-lg">
              PID: 8492
            </span>
          </div>
        </div>

        {/* Input Settings Grid */}
        <div className="grid grid-cols-2 gap-4 mt-2">
          
          {/* Action Delay (Khoảng nghỉ giữa các đòn) */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col justify-between transition-all duration-300 hover:border-slate-700/50">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400">
                  <Clock className="w-4 h-4" />
                </div>
                <label className="text-sm font-bold text-slate-200 tracking-wide">
                  Khoảng nghỉ giữa các đòn
                </label>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed pr-4">
                Độ trễ tối thiểu giữa mỗi chuỗi combo đòn đánh. Đơn vị tính theo số lượng khung hình (frames) tại 60 FPS.
              </p>
            </div>
            
            <div className="relative w-full mt-4">
              <input
                type="number"
                min="0"
                max="300"
                value={delayFrames}
                onChange={(e) => setDelayFrames(Math.max(0, parseInt(e.target.value) || 0))}
                className="w-full pl-4 pr-16 py-3 bg-slate-900/60 rounded-xl border border-slate-800 focus:border-cyan-500/80 focus:ring-1 focus:ring-cyan-500/30 text-white font-mono font-bold text-sm outline-none transition-all"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-500 pointer-events-none select-none tracking-wider">
                frames
              </span>
            </div>
          </div>

          {/* Player 2 Side Selection (Toggle Right/Left) */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col justify-between transition-all duration-300 hover:border-slate-700/50">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400">
                  <Cpu className="w-4 h-4" />
                </div>
                <label className="text-sm font-bold text-slate-200 tracking-wide">
                  Player 2 Side
                </label>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed pr-4">
                Đặt vị trí xuất phát cho Player 2. Ảnh hưởng đến chiều xoay các đòn thế combo dạng nửa vòng (236/214).
              </p>
            </div>
            
            <button
              onClick={() => setIsPlayer2Right(!isPlayer2Right)}
              className="w-full mt-4 flex items-center justify-between py-3 px-4 rounded-xl border border-slate-800 bg-slate-900/60 text-sm font-bold transition-all duration-300 hover:border-cyan-500/40 hover:bg-slate-900"
            >
              <span className="text-slate-400">Bên xuất phát:</span>
              <span className={`text-xs font-bold uppercase px-3 py-1 rounded-lg ${
                isPlayer2Right
                  ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/20'
                  : 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/20'
              }`}>
                {isPlayer2Right ? 'RIGHT (Facing Left)' : 'LEFT (Facing Right)'}
              </span>
            </button>
          </div>

          {/* Combo Set Selection Dropdown */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col justify-between transition-all duration-300 hover:border-slate-700/50">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400">
                  <Keyboard className="w-4 h-4" />
                </div>
                <label className="text-sm font-bold text-slate-200 tracking-wide">
                  Active Combo Set (Playlist)
                </label>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed pr-4">
                Lựa chọn bộ combo đòn đánh đã nạp sẵn từ file cấu hình. Bot sẽ chọn ngẫu nhiên các đòn trong danh sách này để thi triển.
              </p>
            </div>
            
            <div className="relative w-full mt-4">
              <select
                value={selectedComboSet}
                onChange={(e) => setSelectedComboSet(e.target.value)}
                className="w-full px-4 py-3 bg-slate-900/60 rounded-xl border border-slate-800 focus:border-cyan-500/80 focus:ring-1 focus:ring-cyan-500/30 text-white font-bold text-xs outline-none transition-all appearance-none cursor-pointer"
              >
                {playlists.map(name => (
                  <option key={name} value={name} className="bg-slate-950 text-white py-2">
                    {name.toUpperCase()}
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 flex items-center text-slate-500">
                ▼
              </div>
            </div>
          </div>

          {/* Start / Stop Hotkey config */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col justify-between transition-all duration-300 hover:border-slate-700/50">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400">
                  <Keyboard className="w-4 h-4" />
                </div>
                <label className="text-sm font-bold text-slate-200 tracking-wide">
                  Phím tắt Start / Stop Bot
                </label>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Click vào ô hotkey cần cấu hình rồi bấm phím bất kỳ trên bàn phím của bạn để đặt phím tắt kích hoạt nhanh toàn cục.
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-3 mt-4">
              <div>
                <label className="text-[10px] text-slate-500 block mb-1 font-bold">START HOTKEY</label>
                <button
                  onClick={() => setListeningFor('start')}
                  className={`w-full py-2.5 px-3 rounded-lg border text-xs font-bold transition-all duration-300 ${
                    listeningFor === 'start'
                      ? 'bg-cyan-500/15 border-cyan-400 text-cyan-400 animate-pulse'
                      : 'bg-slate-900/60 border-slate-800 text-cyan-400 hover:border-cyan-500/40'
                  }`}
                >
                  {listeningFor === 'start' ? 'BẤM PHÍM...' : startHotkey}
                </button>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 block mb-1 font-bold">STOP HOTKEY</label>
                <button
                  onClick={() => setListeningFor('stop')}
                  className={`w-full py-2.5 px-3 rounded-lg border text-xs font-bold transition-all duration-300 ${
                    listeningFor === 'stop'
                      ? 'bg-cyan-500/15 border-cyan-400 text-cyan-400 animate-pulse'
                      : 'bg-slate-900/60 border-slate-800 text-rose-400 hover:border-rose-500/40'
                  }`}
                >
                  {listeningFor === 'stop' ? 'BẤM PHÍM...' : stopHotkey}
                </button>
              </div>
            </div>
          </div>

        </div>

      </div>

      {/* Save status notification bubble */}
      {saveStatus && (
        <div className={`absolute bottom-24 right-8 px-4 py-3 rounded-xl border text-xs font-bold flex items-center gap-2 animate-bounce shadow-xl ${
          saveStatus === 'saving' ? 'bg-slate-900 border-cyan-500/30 text-cyan-400' :
          saveStatus === 'success' ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-400 shadow-emerald-900/10' :
          'bg-slate-900 border-slate-800 text-slate-400'
        }`}>
          {saveStatus === 'saving' && <div className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />}
          {saveStatus === 'success' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
          {saveStatus === 'saving' && 'Đang gửi cấu hình tới Python...'}
          {saveStatus === 'success' && 'Đã lưu cấu hình chung thành công!'}
          {saveStatus === 'error' && 'Lỗi không thể lưu cấu hình!'}
        </div>
      )}

      {/* Action Buttons Section */}
      <div className="w-full max-w-4xl mx-auto pt-4 mt-4 border-t border-slate-800/40 flex justify-end gap-3.5 shrink-0 bg-[#030712]/40 backdrop-blur-sm z-10">
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs tracking-wider transition-all duration-300 shadow-lg shadow-cyan-500/15 hover:shadow-cyan-400/25 active:scale-[0.98]"
        >
          <Save className="w-4 h-4" />
          LƯU CẤU HÌNH
        </button>
      </div>
    </div>
  );
};

export default SettingsPanel;
