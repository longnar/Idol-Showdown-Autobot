import React, { createContext, useContext, useState, useEffect } from 'react';

const BotContext = createContext();

export const useBot = () => {
  const context = useContext(BotContext);
  if (!context) {
    throw new Error('useBot must be used within a BotProvider');
  }
  return context;
};

export const BotProvider = ({ children }) => {
  // 1. STATE FOR PLAYER 2 INPUT (Frame 2)
  const [bindings, setBindings] = useState({
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
    Grab: 'g'
  });

  // 2. STATE FOR MAIN SETTINGS (Frame 1)
  const [settings, setSettings] = useState({
    gameStatus: 'Stopped', // 'Active' | 'Stopped'
    delayFrames: 30,
    isPlayer2Right: true,
    selectedComboSet: 'test_1',
    startHotkey: 'F9',
    stopHotkey: 'F10',
    gameProcess: '',
    gameWindow: ''
  });

  // 3. PLAYLISTS & COMBOS STATE (Frame 3 & 4)
  const [playlists, setPlaylists] = useState(['test_1', 'pressure_string', 'corner_combo']);
  
  const [combos, setCombos] = useState([]);

  // 4. SYSTEM LOGS & BOT RUNNING STATE
  const [logs, setLogs] = useState([]);
  const [botActive, setBotActive] = useState(false);
  const [activePlaylist, setActivePlaylist] = useState(null);
  const [gameStatus, setGameStatus] = useState({
    running: false,
    focused: false,
    pid: null
  });

  // Helper log in client
  const addLog = (type, msg) => {
    setLogs(prev => [
      { timestamp: new Date().toLocaleTimeString(), type, msg },
      ...prev.slice(0, 49)
    ]);
  };

  // 5. API FETCH AND POLLING HOOKS
  useEffect(() => {
    // Initial data load
    const loadInitialData = async () => {
      try {
        // Load Settings & Bindings
        const configRes = await fetch('/api/config');
        if (configRes.ok) {
          const configData = await configRes.json();
          setSettings(configData.settings);
          setBindings(configData.bindings);
        }
        
        // Load Combos & Playlists
        const comboRes = await fetch('/api/combos');
        if (comboRes.ok) {
          const comboData = await comboRes.json();
          setCombos(comboData.combos);
          setPlaylists(comboData.playlists);
        }

        // Load Status & Logs
        const logsRes = await fetch('/api/logs');
        if (logsRes.ok) {
          const logsData = await logsRes.json();
          setLogs(logsData);
        }

        const statusRes = await fetch('/api/status');
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          setGameStatus({
            running: statusData.game_running,
            focused: statusData.game_focused,
            pid: statusData.game_pid
          });
        }

        const botRes = await fetch('/api/bot/status');
        if (botRes.ok) {
          const botData = await botRes.json();
          setBotActive(botData.running);
          setActivePlaylist(botData.active_playlist);
        }
      } catch (err) {
        console.error("Lỗi tải dữ liệu cấu hình ban đầu:", err);
      }
    };

    loadInitialData();

    // Setup polling every 1 second for logs and bot status
    const interval = setInterval(async () => {
      try {
        const botRes = await fetch('/api/bot/status');
        if (botRes.ok) {
          const botData = await botRes.json();
          setBotActive(botData.running);
          setActivePlaylist(botData.active_playlist);
        }
        
        const logsRes = await fetch('/api/logs');
        if (logsRes.ok) {
          const logsData = await logsRes.json();
          setLogs(logsData);
        }

        const statusRes = await fetch('/api/status');
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          setGameStatus({
            running: statusData.game_running,
            focused: statusData.game_focused,
            pid: statusData.game_pid
          });
        }
      } catch (err) {
        console.error("Lỗi đồng bộ định kỳ:", err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // 6. REAL API IMPLEMENTATIONS

  // A. Start / Stop Python Bot loop
  const startBot = async () => {
    try {
      const res = await fetch('/api/bot/start', { method: 'POST' });
      if (res.ok) {
        setBotActive(true);
        return true;
      }
    } catch (err) {
      console.error(err);
    }
    return false;
  };

  const stopBot = async () => {
    try {
      const res = await fetch('/api/bot/stop', { method: 'POST' });
      if (res.ok) {
        setBotActive(false);
        return true;
      }
    } catch (err) {
      console.error(err);
    }
    return false;
  };

  // B. Lưu cấu hình chung (Frame 1)
  const saveGeneralSettings = async (updatedSettings) => {
    const payload = {
      game_process: updatedSettings.gameProcess,
      game_window: updatedSettings.gameWindow,
      is_player2_right: updatedSettings.isPlayer2Right,
      delay_frames: updatedSettings.delayFrames,
      start_hotkey: updatedSettings.startHotkey,
      stop_hotkey: updatedSettings.stopHotkey,
      selected_playlist: updatedSettings.selectedComboSet
    };

    try {
      const res = await fetch('/api/save_config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setSettings(prev => ({ ...prev, ...updatedSettings }));
        return true;
      }
    } catch (err) {
      console.error("Lỗi khi lưu cấu hình chung:", err);
    }
    return false;
  };

  // C. Lưu phím điều khiển Player 2 (Frame 2)
  const savePlayer2Bindings = async (updatedBindings) => {
    const payload = {
      bindings: {
        Up: updatedBindings.Jump,
        Down: updatedBindings.Crouch,
        Left: updatedBindings.Left,
        Right: updatedBindings.Right,
        Light: updatedBindings.Light,
        Medium: updatedBindings.Medium,
        Heavy: updatedBindings.Heavy,
        Special: updatedBindings.Special,
        Collab: updatedBindings.Collab,
        Burst: updatedBindings.Burst,
        Items: updatedBindings.Items,
        Grab: updatedBindings.Grab
      }
    };

    try {
      const res = await fetch('/api/save_p2_bindings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setBindings(updatedBindings);
        return true;
      }
    } catch (err) {
      console.error("Lỗi khi lưu phím điều khiển:", err);
    }
    return false;
  };

  // D. Kích hoạt kiểm thử Combo (Frame 3)
  const testCombo = async (comboSequence, isNumpad) => {
    const payload = {
      combo_sequence: comboSequence,
      is_numpad: isNumpad
    };

    try {
      const res = await fetch('/api/test_combo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        return data;
      }
    } catch (err) {
      console.error("Lỗi khi test combo:", err);
    }
    return {
      success: false,
      notice: `[LỖI] Không thể gửi gói tin kiểm thử đến Python backend.`
    };
  };

  // E. Tạo Playlist mới
  const createPlaylist = async (name) => {
    try {
      const res = await fetch('/api/create_playlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });
      if (res.ok) {
        const comboRes = await fetch('/api/combos');
        if (comboRes.ok) {
          const comboData = await comboRes.json();
          setCombos(comboData.combos);
          setPlaylists(comboData.playlists);
        }
        return { success: true };
      } else {
        const errData = await res.json();
        return { success: false, message: errData.message || "Lỗi tạo playlist" };
      }
    } catch (err) {
      console.error("Lỗi khi tạo playlist:", err);
      return { success: false, message: "Lỗi kết nối server" };
    }
  };

  // F. Lưu Combo mới / chỉnh sửa vào List (Frame 3 & 4)
  const saveComboToList = async (newCombo) => {
    try {
      const res = await fetch('/api/save_combo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newCombo)
      });
      if (res.ok) {
        // Tải lại toàn bộ combos mới từ backend
        const comboRes = await fetch('/api/combos');
        if (comboRes.ok) {
          const comboData = await comboRes.json();
          setCombos(comboData.combos);
          setPlaylists(comboData.playlists);
        }
        return true;
      }
    } catch (err) {
      console.error("Lỗi khi lưu combo:", err);
    }
    return false;
  };

  // F. Xóa Combo khỏi List (Frame 4)
  const deleteComboFromList = async (id) => {
    try {
      const res = await fetch(`/api/delete_combo?id=${id}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        const comboRes = await fetch('/api/combos');
        if (comboRes.ok) {
          const comboData = await comboRes.json();
          setCombos(comboData.combos);
          setPlaylists(comboData.playlists);
        }
        return true;
      }
    } catch (err) {
      console.error("Lỗi khi xóa combo:", err);
    }
    return false;
  };

  // G. Chọn Combo để kích hoạt thi triển ngay (Frame 4)
  const selectComboToPlay = async (combo) => {
    try {
      const res = await fetch('/api/select_combo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(combo)
      });
      return res.ok;
    } catch (err) {
      console.error("Lỗi khi thi triển nhanh:", err);
    }
    return false;
  };

  return (
    <BotContext.Provider value={{
      bindings,
      setBindings,
      settings,
      setSettings,
      playlists,
      setPlaylists,
      combos,
      setCombos,
      logs,
      addLog,
      botActive,
      activePlaylist,
      gameStatus,
      startBot,
      stopBot,
      saveGeneralSettings,
      savePlayer2Bindings,
      testCombo,
      saveComboToList,
      deleteComboFromList,
      selectComboToPlay,
      createPlaylist
    }}>
      {children}
    </BotContext.Provider>
  );
};
