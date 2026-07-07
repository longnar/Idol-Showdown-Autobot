import React, { useState, useEffect } from 'react';
import { useBot } from './BotContext';
import { Save, Info, Cpu, CheckCircle, Keyboard, RefreshCw } from 'lucide-react';

const Player2InputPanel = () => {
  const { bindings, savePlayer2Bindings } = useBot();

  // Local state to hold temporary edits
  const [localBindings, setLocalBindings] = useState({ ...bindings });

  // Synced from context if global state changes
  useEffect(() => {
    setLocalBindings({ ...bindings });
  }, [bindings]);

  // Trạng thái theo dõi phím nào đang chờ lắng nghe sự kiện nhấn bàn phím
  const [listeningAction, setListeningAction] = useState(null);
  
  // Trạng thái hiển thị thông báo khi lưu thành công hoặc đặt lại mặc định
  const [saveStatus, setSaveStatus] = useState(null);

  // 2. LISTEN FOR KEYPRESSES TO CAPTURE INPUT (Tính năng Capture Key)
  useEffect(() => {
    if (!listeningAction) return;

    const handleKeyDown = (e) => {
      // Ngăn chặn các sự kiện mặc định của trình duyệt như cuộn trang bằng phím mũi tên hoặc Space
      e.preventDefault();
      e.stopPropagation();
      
      let keyName = e.key;
      
      // Ánh xạ các phím đặc biệt sang định dạng tương thích với các phím ảo của Python
      if (keyName === ' ') keyName = 'space';
      else if (keyName === 'ArrowUp') keyName = 'up';
      else if (keyName === 'ArrowDown') keyName = 'down';
      else if (keyName === 'ArrowLeft') keyName = 'left';
      else if (keyName === 'ArrowRight') keyName = 'right';
      else if (keyName === 'Control') keyName = 'ctrl';
      else if (keyName === 'Escape') keyName = 'esc';
      else if (keyName === 'Backspace') keyName = 'backspace';
      else if (keyName === 'Tab') keyName = 'tab';
      else if (keyName === 'Shift') keyName = 'shift';
      else if (keyName === 'Alt') keyName = 'alt';
      else if (keyName === 'Enter') keyName = 'enter';

      // Chuyển ký tự đơn sang chữ thường (định dạng khớp với file config.json)
      if (keyName.length === 1) {
        keyName = keyName.toLowerCase();
      }

      setLocalBindings(prev => ({
        ...prev,
        [listeningAction]: keyName
      }));
      setListeningAction(null);
    };

    // Đăng ký bắt sự kiện ở capture phase để ngăn nhiễu
    window.addEventListener('keydown', handleKeyDown, true);
    return () => {
      window.removeEventListener('keydown', handleKeyDown, true);
    };
  }, [listeningAction]);

  // Hàm chuyển đổi phím hiển thị cho giao diện trực quan hơn
  const formatKeyDisplay = (key) => {
    if (!key) return 'NONE';
    switch(key.toLowerCase()) {
      case 'space': return 'SPACE';
      case 'up': return '▲ UP';
      case 'down': return '▼ DOWN';
      case 'left': return '◀ LEFT';
      case 'right': return '▶ RIGHT';
      case 'ctrl': return 'CTRL';
      case 'shift': return 'SHIFT';
      case 'alt': return 'ALT';
      case 'enter': return 'ENTER';
      case 'backspace': return 'BACKSPACE';
      case 'tab': return 'TAB';
      case 'esc': return 'ESC';
      default: return key.toUpperCase();
    }
  };

  // 3. ACTION HANDLERS (Xử lý Lưu & Đặt lại)
  const handleSave = async () => {
    setSaveStatus('saving');
    
    // Gọi hàm lưu của context để gửi payload tới Python
    const success = await savePlayer2Bindings(localBindings);

    if (success) {
      setSaveStatus('success');
      // Thêm chức năng tải xuống config.json như yêu cầu
      try {
        const configData = {
          bindings: {
            Up: localBindings.Jump.toLowerCase(),
            Down: localBindings.Crouch.toLowerCase(),
            Left: localBindings.Left.toLowerCase(),
            Right: localBindings.Right.toLowerCase(),
            Light: localBindings.Light.toLowerCase(),
            Medium: localBindings.Medium.toLowerCase(),
            Heavy: localBindings.Heavy.toLowerCase(),
            Special: localBindings.Special.toLowerCase(),
            Collab: localBindings.Collab.toLowerCase(),
            Burst: localBindings.Burst.toLowerCase(),
            Items: localBindings.Items.toLowerCase(),
            Grap: localBindings.Grap.toLowerCase()
          },
          game_process: "Idol Showdown.exe",
          game_window: "Idol Showdown",
          is_player2_right: true
        };

        const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(
          JSON.stringify(configData, null, 4)
        )}`;
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute('href', jsonString);
        downloadAnchor.setAttribute('download', 'config.json');
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
      } catch (err) {
        console.error("Lỗi khi tạo file download cấu hình:", err);
      }

      setTimeout(() => setSaveStatus(null), 3000);
    } else {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus(null), 3000);
    }
  };

  const handleReset = () => {
    // Reset về trạng thái phím mặc định của bot
    setLocalBindings({
      Jump: 'w',
      Crouch: 's',
      Left: 'a',
      Right: 'd',
      Light: 'j',
      Medium: 'k',
      Heavy: 'l',
      Special: 'i',
      Collab: 'o',
      Burst: 'u',
      Items: 'h',
      Grap: 'g'
    });
    setSaveStatus('reset');
    setTimeout(() => setSaveStatus(null), 2500);
  };

  // Group columns for rendering
  const column1 = [
    { label: 'Nhảy (Jump)', key: 'Jump', desc: 'Di chuyển lên / Nhảy' },
    { label: 'Ngồi (Crouch)', key: 'Crouch', desc: 'Di chuyển xuống / Ngồi' },
    { label: 'Trái (Left)', key: 'Left', desc: 'Di chuyển sang trái' },
    { label: 'Phải (Right)', key: 'Right', desc: 'Di chuyển sang phải' },
    { label: 'Đòn Nhẹ (Light)', key: 'Light', desc: 'Tấn công nhẹ (Punch)' },
    { label: 'Đòn Trung (Medium)', key: 'Medium', desc: 'Tấn công vừa (Kick)' },
    { label: 'Đòn Mạnh (Heavy)', key: 'Heavy', desc: 'Tấn công mạnh (Slash)' },
    { label: 'Đặc biệt (Special)', key: 'Special', desc: 'Chiêu thức đặc biệt' },
  ];

  const column2 = [
    { label: 'Hỗ trợ (Collab)', key: 'Collab', desc: 'Gọi nhân vật hỗ trợ' },
    { label: 'Bộc phá (Burst)', key: 'Burst', desc: 'Kích hoạt thanh nổ / Burst' },
    { label: 'Vật phẩm (Items)', key: 'Items', desc: 'Sử dụng vật phẩm nhặt' },
    { label: 'Vật/Ném (Grap)', key: 'Grap', desc: 'Đòn vật / Bắt lấy đối thủ' },
  ];

  return (
    <div className="flex-1 flex flex-col justify-between p-6 scanline-bg relative h-full overflow-hidden">
      {/* Hiệu ứng phát sáng nền */}
      <div className="absolute top-1/4 right-1/4 w-96 h-96 rounded-full bg-cyan-500/5 blur-[120px] pointer-events-none pulse-glow-circle" />

      {/* Khối giao diện cấu hình */}
      <div className="flex-1 overflow-y-auto max-w-4xl w-full mx-auto flex flex-col gap-5 pr-2">
        
        {/* Tiêu đề & Giới thiệu */}
        <div>
          <div className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 animate-pulse" /> BẢNG CÀI ĐẶT PHÍM
          </div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Keyboard className="w-6 h-6 text-cyan-400" /> Player 2 Input Key Bindings
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Chỉ định 12 phím hoạt động chính cho Player 2. Click vào ô nhập liệu rồi gõ phím bất kỳ trên bàn phím.
          </p>
        </div>

        {/* Khung mô tả kết nối Backend */}
        <div className="p-4 rounded-xl bg-slate-900/30 border border-slate-800/40 text-xs text-slate-400 flex gap-3 items-start">
          <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-slate-300">Hướng dẫn tích hợp với file config.json của Python:</p>
            <p className="mt-1 text-[11px] leading-relaxed">
              Các phím di chuyển <span className="text-slate-200 font-bold">Jump</span> và <span className="text-slate-200 font-bold">Crouch</span> 
              sẽ được lưu tự động thành các khóa <span className="font-mono text-cyan-400">"Up"</span> và <span className="font-mono text-cyan-400">"Down"</span> trong JSON 
              để đồng bộ hoàn hảo với module Python <span className="font-mono text-cyan-400">config_manager.py</span> hiện có của bạn.
            </p>
          </div>
        </div>

        {/* Bảng nhập liệu: Grid 2 cột */}
        <div className="grid grid-cols-2 gap-6 mt-2">
          
          {/* Cột 1: Di chuyển & Tấn công */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col justify-between transition-all duration-300 hover:border-slate-700/50">
            <div>
              <h3 className="text-sm font-bold text-cyan-400 mb-4 border-b border-slate-800 pb-2 tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
                CỘT 1: DI CHUYỂN & TẤN CÔNG
              </h3>
              
              <div className="flex flex-col gap-3">
                {column1.map((item) => (
                  <div key={item.key} className="flex items-center justify-between gap-4 py-2 border-b border-slate-800/20 last:border-0">
                    <div className="flex flex-col">
                      <span className="text-xs font-bold text-slate-200">{item.label}</span>
                      <span className="text-[10px] text-slate-500">{item.desc}</span>
                    </div>
                    
                    <div className="w-36 shrink-0">
                      <input
                        type="text"
                        readOnly
                        value={listeningAction === item.key ? 'ĐANG CHỜ BẤM...' : formatKeyDisplay(localBindings[item.key])}
                        onClick={() => setListeningAction(item.key)}
                        placeholder="Click to bind"
                        className={`w-full text-center py-2 px-3 rounded-lg border font-mono font-bold text-xs outline-none transition-all duration-300 cursor-pointer ${
                          listeningAction === item.key
                            ? 'bg-cyan-500/15 border-cyan-400 text-cyan-400 animate-pulse shadow-[0_0_10px_rgba(6,182,212,0.2)]'
                            : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-cyan-500/40 hover:text-white focus:border-cyan-500'
                        }`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Cột 2: Hành động đặc biệt */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col justify-between transition-all duration-300 hover:border-slate-700/50">
            <div>
              <h3 className="text-sm font-bold text-cyan-400 mb-4 border-b border-slate-800 pb-2 tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
                CỘT 2: HÀNH ĐỘNG ĐẶC BIỆT
              </h3>
              
              <div className="flex flex-col gap-3">
                {column2.map((item) => (
                  <div key={item.key} className="flex items-center justify-between gap-4 py-2 border-b border-slate-800/20 last:border-0">
                    <div className="flex flex-col">
                      <span className="text-xs font-bold text-slate-200">{item.label}</span>
                      <span className="text-[10px] text-slate-500">{item.desc}</span>
                    </div>
                    
                    <div className="w-36 shrink-0">
                      <input
                        type="text"
                        readOnly
                        value={listeningAction === item.key ? 'ĐANG CHỜ BẤM...' : formatKeyDisplay(localBindings[item.key])}
                        onClick={() => setListeningAction(item.key)}
                        placeholder="Click to bind"
                        className={`w-full text-center py-2 px-3 rounded-lg border font-mono font-bold text-xs outline-none transition-all duration-300 cursor-pointer ${
                          listeningAction === item.key
                            ? 'bg-cyan-500/15 border-cyan-400 text-cyan-400 animate-pulse shadow-[0_0_10px_rgba(6,182,212,0.2)]'
                            : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-cyan-500/40 hover:text-white focus:border-cyan-500'
                        }`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Chú thích code Python chi tiết để tích hợp */}
            <div className="mt-6 p-4 bg-cyan-950/20 border border-cyan-900/30 rounded-xl text-[10px] text-cyan-400/80 font-mono flex flex-col gap-1 leading-relaxed">
              <div># HƯỚNG DẪN ĐỌC FILE BẰNG PYTHON:</div>
              <div>import json</div>
              <div>def load_p2_bindings(filepath="config.json"):</div>
              <div className="pl-4">with open(filepath, 'r', encoding='utf-8') as f:</div>
              <div className="pl-8">config = json.load(f)</div>
              <div className="pl-8"># Trả về các nút tương thích với input_mapper</div>
              <div className="pl-8">return config["bindings"]</div>
            </div>
          </div>

        </div>

      </div>

      {/* Thông báo trạng thái lưu */}
      {saveStatus && (
        <div className={`absolute bottom-24 right-8 px-4 py-3 rounded-xl border text-xs font-bold flex items-center gap-2 animate-bounce shadow-xl ${
          saveStatus === 'saving' ? 'bg-slate-900 border-cyan-500/30 text-cyan-400' :
          saveStatus === 'success' ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-400 shadow-emerald-900/10' :
          'bg-slate-900 border-slate-800 text-slate-400'
        }`}>
          {saveStatus === 'saving' && <div className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />}
          {saveStatus === 'success' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
          {saveStatus === 'saving' && 'Đang gửi phím điều khiển...'}
          {saveStatus === 'success' && 'Đã tải xuống config.json & đồng bộ thành công!'}
          {saveStatus === 'reset' && 'Đã thiết lập lại cấu hình mặc định.'}
        </div>
      )}

      {/* Nút lưu góc dưới bên phải */}
      <div className="w-full max-w-4xl mx-auto pt-4 mt-4 border-t border-slate-800/40 flex justify-end gap-3.5 shrink-0 bg-[#030712]/40 backdrop-blur-sm z-10">
        <button
          onClick={handleReset}
          className="flex items-center gap-2 px-5 py-3 rounded-xl border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800/40 hover:border-slate-700 transition-all text-xs font-bold tracking-wider"
        >
          <RefreshCw className="w-4 h-4" />
          ĐẶT LẠI MẶC ĐỊNH
        </button>
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold text-xs tracking-wider transition-all duration-300 shadow-lg shadow-cyan-500/15 hover:shadow-cyan-400/25 active:scale-[0.98]"
        >
          <Save className="w-4 h-4" />
          LƯU CÀI ĐẶT
        </button>
      </div>
    </div>
  );
};

export default Player2InputPanel;
