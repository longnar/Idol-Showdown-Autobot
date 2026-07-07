import React, { useState } from 'react';
import { useBot } from './BotContext';
import { HelpCircle, Play, Save, Info, Cpu, CheckCircle } from 'lucide-react';

const ComboCustomPanel = () => {
  const { playlists, testCombo, saveComboToList } = useBot();

  // Form states
  const [comboName, setComboName] = useState('');
  const [comboInput, setComboInput] = useState('');
  const [isNumpad, setIsNumpad] = useState(true);
  const [selectedPlaylist, setSelectedPlaylist] = useState(playlists[0] || 'test_1');
  
  // Test console logs / status notice (read-only)
  const [testNotice, setTestNotice] = useState('Chưa chạy thử nghiệm nào. Nhập combo và nhấn nút "TEST THỬ NGHIỆM" bên dưới.');
  const [isTesting, setIsTesting] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  const handleTest = async () => {
    if (!comboInput.trim()) {
      setTestNotice('[LỖI] Chuỗi combo không được trống!');
      return;
    }
    
    setIsTesting(true);
    setTestNotice('[CONNECTING] Gửi combo đến Python execution engine...');
    
    const response = await testCombo(comboInput, isNumpad);
    
    setIsTesting(false);
    if (response && response.success) {
      setTestNotice(response.notice || `[TEST OK] Thực thi combo thành công: "${comboInput}"`);
    } else {
      setTestNotice(response?.notice || `[TEST ERROR] Thực thi thất bại! Hãy kiểm tra log Python.`);
    }
  };

  const handleSave = async () => {
    if (!comboName.trim()) {
      alert('Vui lòng nhập tên cho Combo này!');
      return;
    }
    if (!comboInput.trim()) {
      alert('Vui lòng nhập chuỗi nút của Combo!');
      return;
    }

    setSaveStatus('saving');
    const success = await saveComboToList({
      name: comboName,
      input: comboInput,
      playlist: selectedPlaylist
    });

    if (success) {
      setSaveStatus('success');
      setComboName('');
      setComboInput('');
      setTimeout(() => setSaveStatus(null), 3000);
    } else {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  return (
    <div className="flex-1 flex flex-col justify-between p-6 scanline-bg relative h-full overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/4 right-1/4 w-96 h-96 rounded-full bg-cyan-500/5 blur-[120px] pointer-events-none pulse-glow-circle" />

      <div className="flex-1 overflow-y-auto max-w-4xl w-full mx-auto flex flex-col gap-5 pr-2">
        
        {/* Title */}
        <div>
          <div className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5" /> COMBO EDITOR
          </div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            Thiết kế & Tùy chỉnh Combo
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Tự soạn các tổ hợp chiêu thức mới, chạy thử nghiệm tức thời lên cửa sổ game và lưu vào danh sách phát.
          </p>
        </div>

        {/* Instructions & Manual */}
        <div className="p-4 rounded-xl bg-slate-900/30 border border-slate-800/40 text-xs text-slate-400 flex gap-3 items-start">
          <HelpCircle className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-slate-200">Hướng dẫn ghi ký tự Combo (Move Notation):</p>
            <p className="mt-1 text-[11px] leading-relaxed">
              • <span className="text-cyan-400 font-semibold">Numpad notation (Mặc định)</span>: Sử dụng số (1-9) cho hướng di chuyển (Tương ứng với các phím mũi tên trên Numpad: 6=Tiến, 4=Lùi, 2=Xuống, 8=Lên, 5=Đứng yên) kết hợp nút tấn công: <span className="font-bold text-slate-300">L, M, H, S, B, CL</span>. Ví dụ: <span className="font-mono text-cyan-400">236H</span> (Hadouken), <span className="font-mono text-cyan-400">623H</span> (Shoryuken).
            </p>
            <p className="mt-1 text-[11px] leading-relaxed">
              • <span className="text-cyan-400 font-semibold">Action name mode</span>: Viết rõ tên nút hành động của bạn. Ví dụ: <span className="font-mono text-cyan-400">Down, Down-Left, Left + Light</span>.
            </p>
            <p className="mt-1 text-[11px] leading-relaxed">
              • Dùng dấu <span className="font-bold text-slate-300">+</span> để ấn đồng thời các phím (Ví dụ: <span className="font-mono text-cyan-400">2+H</span>), dấu <span className="font-bold text-slate-300">,</span> để tách biệt các bước combo (Ví dụ: <span className="font-mono text-cyan-400">5L, 5M, 236H</span>).
            </p>
          </div>
        </div>

        {/* Input and Testing layout */}
        <div className="grid grid-cols-2 gap-6 mt-2">
          
          {/* Form soan combo */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col gap-4 justify-between transition-all duration-300 hover:border-slate-700/50">
            <div className="flex flex-col gap-4">
              <h3 className="text-sm font-bold text-cyan-400 border-b border-slate-800 pb-2 tracking-wider">
                THÔNG TIN CHIÊU THỨC
              </h3>
              
              {/* Combo Name */}
              <div>
                <label className="text-[10px] text-slate-500 block mb-1 font-bold uppercase">Tên combo (Ví dụ: Hadouken)</label>
                <input
                  type="text"
                  placeholder="Nhập tên combo..."
                  value={comboName}
                  onChange={(e) => setComboName(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-900/60 rounded-xl border border-slate-800 text-white font-bold text-xs outline-none focus:border-cyan-500 transition-all"
                />
              </div>

              {/* Toggle Input Notation */}
              <div className="flex items-center gap-3">
                <input
                  id="notation-checkbox"
                  type="checkbox"
                  checked={isNumpad}
                  onChange={(e) => setIsNumpad(e.target.checked)}
                  className="w-4 h-4 accent-cyan-500 rounded border-slate-800 bg-slate-900 focus:ring-0 focus:ring-offset-0 cursor-pointer"
                />
                <label htmlFor="notation-checkbox" className="text-xs text-slate-300 font-medium select-none cursor-pointer">
                  Sử dụng ký hiệu Numpad Notation (e.g. 236L)
                </label>
              </div>

              {/* Combo Textarea */}
              <div>
                <label className="text-[10px] text-slate-500 block mb-1 font-bold uppercase">Chuỗi nút thi triển</label>
                <textarea
                  rows={4}
                  placeholder={isNumpad ? 'Ví dụ: 236H, 5L, 214M' : 'Ví dụ: Down, Right + Heavy'}
                  value={comboInput}
                  onChange={(e) => setComboInput(e.target.value)}
                  className="w-full p-4 bg-slate-900/60 rounded-xl border border-slate-800 text-white font-mono text-xs outline-none focus:border-cyan-500 transition-all resize-none"
                />
              </div>
            </div>

            {/* Test button & Save target dropdown */}
            <div className="flex flex-col gap-3 mt-2">
              <div className="flex items-center justify-between gap-3">
                <div className="flex-1">
                  <label className="text-[10px] text-slate-500 block mb-1 font-bold uppercase">Lưu vào danh sách phát</label>
                  <select
                    value={selectedPlaylist}
                    onChange={(e) => setSelectedPlaylist(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900/60 rounded-lg border border-slate-800 text-white font-bold text-[11px] outline-none cursor-pointer appearance-none"
                  >
                    {playlists.map(name => (
                      <option key={name} value={name} className="bg-slate-950 text-white">
                        {name.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="self-end shrink-0">
                  <button
                    onClick={handleTest}
                    disabled={isTesting}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-cyan-400 hover:text-cyan-300 hover:bg-slate-700 hover:border-slate-600 text-xs font-bold transition-all"
                  >
                    <Play className="w-3.5 h-3.5 fill-cyan-400" />
                    TEST COMBO
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Test Notice & Output status */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col justify-between transition-all duration-300 hover:border-slate-700/50">
            <div>
              <h3 className="text-sm font-bold text-cyan-400 mb-4 border-b border-slate-800 pb-2 tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
                TESTING INPUT NOTICE (KẾT QUẢ TEST)
              </h3>
              
              <div 
                className={`w-full min-h-[160px] p-4 rounded-xl border font-mono text-[11px] leading-relaxed shadow-inner overflow-y-auto ${
                  testNotice.startsWith('[LỖI]')
                    ? 'bg-rose-950/20 border-rose-900/30 text-rose-400'
                    : testNotice.startsWith('[TEST OK]')
                    ? 'bg-emerald-950/20 border-emerald-900/30 text-emerald-400'
                    : 'bg-black/40 border-slate-850 text-cyan-500/80'
                }`}
              >
                {testNotice}
              </div>
            </div>

            {/* Python Connection Info inside Output Card */}
            <div className="mt-4 p-3 bg-cyan-950/15 border border-cyan-900/25 rounded-xl text-[10px] text-cyan-400/70 font-mono leading-normal">
              <div># PYTHON COMBO INTERFACE API:</div>
              <div># POST /api/test_combo {"{"}</div>
              <div className="pl-4">"combo_sequence": "{comboInput || '236H'}",</div>
              <div className="pl-4">"is_numpad": {String(isNumpad)}</div>
              <div>{"}"}</div>
            </div>
          </div>

        </div>

      </div>

      {/* Alert Status */}
      {saveStatus && (
        <div className={`absolute bottom-24 right-8 px-4 py-3 rounded-xl border text-xs font-bold flex items-center gap-2 animate-bounce shadow-xl ${
          saveStatus === 'saving' ? 'bg-slate-900 border-cyan-500/30 text-cyan-400' :
          saveStatus === 'success' ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-400' :
          'bg-slate-900 border-slate-800 text-slate-400'
        }`}>
          {saveStatus === 'saving' && <div className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />}
          {saveStatus === 'success' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
          {saveStatus === 'saving' && 'Đang lưu combo mới...'}
          {saveStatus === 'success' && 'Đã lưu combo vào danh sách phát thành công!'}
        </div>
      )}

      {/* Save Button */}
      <div className="w-full max-w-4xl mx-auto pt-4 mt-4 border-t border-slate-800/40 flex justify-end gap-3.5 shrink-0 bg-[#030712]/40 backdrop-blur-sm z-10">
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs tracking-wider transition-all duration-300 shadow-lg shadow-cyan-500/15 hover:shadow-cyan-400/25 active:scale-[0.98]"
        >
          <Save className="w-4 h-4" />
          LƯU VÀO LIST
        </button>
      </div>
    </div>
  );
};

export default ComboCustomPanel;
