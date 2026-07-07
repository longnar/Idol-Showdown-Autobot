import React, { useState } from 'react';
import { useBot } from './BotContext';
import { Play, Plus, Edit2, Trash2, Save, X, Cpu, CheckCircle } from 'lucide-react';

const ComboListPanel = () => {
  const { combos, deleteComboFromList, saveComboToList, selectComboToPlay, playlists } = useBot();

  // Active selected row
  const [selectedId, setSelectedId] = useState(combos[0]?.id || null);
  
  // Edit/Create form state
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [formName, setFormName] = useState('');
  const [formInput, setFormInput] = useState('');
  const [formPlaylist, setFormPlaylist] = useState('test_1');

  // Status notification
  const [actionStatus, setActionStatus] = useState(null);

  const selectedCombo = combos.find(c => c.id === selectedId);

  const handleSelect = async () => {
    if (!selectedCombo) return;
    setActionStatus('playing');
    const success = await selectComboToPlay(selectedCombo);
    if (success) {
      setActionStatus('success_play');
      setTimeout(() => setActionStatus(null), 3000);
    } else {
      setActionStatus(null);
    }
  };

  const handleDelete = async () => {
    if (!selectedId) return;
    const confirm = window.confirm('Bạn có chắc chắn muốn xóa combo này khỏi danh sách?');
    if (!confirm) return;

    setActionStatus('deleting');
    const success = await deleteComboFromList(selectedId);
    if (success) {
      setActionStatus('success_delete');
      // Select another combo in the list
      const remaining = combos.filter(c => c.id !== selectedId);
      setSelectedId(remaining[0]?.id || null);
      setTimeout(() => setActionStatus(null), 3000);
    } else {
      setActionStatus(null);
    }
  };

  const startCreate = () => {
    setIsCreating(true);
    setIsEditing(false);
    setFormName('');
    setFormInput('');
    setFormPlaylist(playlists[0] || 'test_1');
  };

  const startEdit = () => {
    if (!selectedCombo) return;
    setIsEditing(true);
    setIsCreating(false);
    setFormName(selectedCombo.name);
    setFormInput(selectedCombo.input);
    setFormPlaylist(selectedCombo.playlist);
  };

  const cancelForm = () => {
    setIsEditing(false);
    setIsCreating(false);
  };

  const handleSaveForm = async () => {
    if (!formName.trim() || !formInput.trim()) {
      alert('Vui lòng nhập đầy đủ tên và nút combo!');
      return;
    }

    setActionStatus('saving');
    const comboPayload = {
      name: formName,
      input: formInput,
      playlist: formPlaylist
    };

    if (isEditing) {
      comboPayload.id = selectedId;
    }

    const success = await saveComboToList(comboPayload);
    if (success) {
      setIsEditing(false);
      setIsCreating(false);
      setActionStatus('success_save');
      setTimeout(() => setActionStatus(null), 3000);
    } else {
      setActionStatus(null);
    }
  };

  return (
    <div className="flex-1 flex flex-col justify-between p-6 scanline-bg relative h-full overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-1/4 right-1/4 w-96 h-96 rounded-full bg-cyan-500/5 blur-[120px] pointer-events-none pulse-glow-circle" />

      <div className="max-w-5xl w-full mx-auto flex-1 flex flex-col gap-4 overflow-hidden">
        
        {/* Title */}
        <div>
          <div className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 animate-pulse" /> MOVE LIST MANAGER
          </div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
            Danh sách đòn đánh & Playlist
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Quản lý, chỉnh sửa hoặc thi triển nhanh toàn bộ các đòn thế/combo đã thiết lập trong hệ thống.
          </p>
        </div>

        {/* 2-column main area: Left table (2 cols), Right actions panel (1 col) */}
        <div className="grid grid-cols-3 gap-6 mt-2 flex-1 overflow-hidden items-stretch">
          
          {/* Table list of combos (col-span-2) */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col justify-between col-span-2 overflow-hidden transition-all duration-300 hover:border-slate-700/50">
            <div className="w-full flex-1 overflow-y-auto pr-1">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-cyan-400/80 text-[10px] uppercase font-bold tracking-wider">
                    <th className="py-2.5 px-3">TÊN COMBO (NAME)</th>
                    <th className="py-2.5 px-3">NÚT LỆNH (INPUT)</th>
                    <th className="py-2.5 px-3 text-right">DANH SÁCH (PLAYLIST)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/30 text-xs">
                  {combos.map((combo) => (
                    <tr
                      key={combo.id}
                      onClick={() => { setSelectedId(combo.id); cancelForm(); }}
                      className={`cursor-pointer transition-colors duration-200 ${
                        selectedId === combo.id
                          ? 'bg-cyan-500/10 border-l-2 border-cyan-400 text-white'
                          : 'text-slate-300 hover:bg-slate-850 hover:text-slate-100'
                      }`}
                    >
                      <td className="py-3 px-3 font-semibold">{combo.name}</td>
                      <td className="py-3 px-3 font-mono text-cyan-400 font-bold">{combo.input}</td>
                      <td className="py-3 px-3 text-right font-semibold text-slate-500 uppercase">{combo.playlist}</td>
                    </tr>
                  ))}
                  {combos.length === 0 && (
                    <tr>
                      <td colSpan="3" className="py-8 text-center text-slate-500 font-medium">
                        Không có combo nào khả dụng. Hãy tạo mới ở panel bên cạnh!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Action buttons below the table */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800/60 mt-3 shrink-0">
              <div className="flex gap-2">
                <button
                  onClick={startCreate}
                  disabled={isCreating}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/20 text-xs font-bold transition-all"
                >
                  <Plus className="w-3.5 h-3.5" />
                  CREATE NEW
                </button>
                <button
                  onClick={startEdit}
                  disabled={!selectedId || isEditing || isCreating}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                  EDIT SELECT
                </button>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleDelete}
                  disabled={!selectedId || isEditing || isCreating}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-rose-950/20 border border-rose-900/30 text-rose-400 hover:text-rose-300 hover:bg-rose-900/20 text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  DELETE
                </button>
                <button
                  onClick={handleSelect}
                  disabled={!selectedId || isEditing || isCreating}
                  className="flex items-center gap-1.5 px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-cyan-500/10"
                >
                  <Play className="w-3.5 h-3.5 fill-white" />
                  EXECUTE SELECT
                </button>
              </div>
            </div>
          </div>

          {/* Form details side card */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/50 flex flex-col justify-between col-span-1 overflow-hidden transition-all duration-300 hover:border-slate-700/50">
            {isCreating || isEditing ? (
              // EDIT / CREATE FORM
              <div className="flex flex-col gap-4 flex-1 justify-between overflow-y-auto pr-1">
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2 shrink-0">
                    <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
                      {isCreating ? 'TẠO MỚI COMBO' : 'CHỈNH SỬA COMBO'}
                    </h3>
                    <button onClick={cancelForm} className="text-slate-500 hover:text-slate-300 shrink-0">
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  <div>
                    <label className="text-[10px] text-slate-500 block mb-1 font-bold uppercase">Tên combo</label>
                    <input
                      type="text"
                      placeholder="e.g. Shoryuken Ex"
                      value={formName}
                      onChange={(e) => setFormName(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900/60 rounded-xl border border-slate-800 text-white font-bold text-xs outline-none focus:border-cyan-500 transition-all"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] text-slate-500 block mb-1 font-bold uppercase">Nút lệnh (Move Sequence)</label>
                    <input
                      type="text"
                      placeholder="e.g. 623CL"
                      value={formInput}
                      onChange={(e) => setFormInput(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900/60 rounded-xl border border-slate-800 text-cyan-400 font-mono font-bold text-xs outline-none focus:border-cyan-500 transition-all"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] text-slate-500 block mb-1 font-bold uppercase">Danh sách phát</label>
                    <select
                      value={formPlaylist}
                      onChange={(e) => setFormPlaylist(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900/60 rounded-xl border border-slate-800 text-white font-bold text-[11px] outline-none cursor-pointer appearance-none"
                    >
                      {playlists.map(name => (
                        <option key={name} value={name} className="bg-slate-950 text-white">
                          {name.toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="flex gap-2 pt-3 border-t border-slate-800/40 shrink-0">
                  <button
                    onClick={cancelForm}
                    className="flex-1 py-2 rounded-lg border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800/40 hover:border-slate-700 text-xs font-bold transition-all"
                  >
                    HỦY BỎ
                  </button>
                  <button
                    onClick={handleSaveForm}
                    className="flex-1 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold transition-all flex items-center justify-center gap-1.5"
                  >
                    <Save className="w-3.5 h-3.5" />
                    LƯU
                  </button>
                </div>
              </div>
            ) : (
              // READ-ONLY / DETAILED VIEW
              <div className="flex flex-col justify-between flex-1 overflow-y-auto pr-1">
                <div>
                  <h3 className="text-xs font-bold text-cyan-400 border-b border-slate-800 pb-2 tracking-wider uppercase mb-4 shrink-0">
                    CHI TIẾT ĐÒN THẾ
                  </h3>
                  {selectedCombo ? (
                    <div className="flex flex-col gap-4">
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase font-bold block">Tên Combo</span>
                        <span className="text-sm font-bold text-white mt-0.5 block">{selectedCombo.name}</span>
                      </div>
                      
                      <div>
                        <span className="text-[10px] text-slate-500 uppercase font-bold block">Nút điều khiển</span>
                        <span className="text-sm font-mono font-bold text-cyan-400 mt-0.5 block bg-slate-950/60 py-2 px-3 rounded-lg border border-slate-900 inline-block">
                          {selectedCombo.input}
                        </span>
                      </div>

                      <div>
                        <span className="text-[10px] text-slate-500 uppercase font-bold block">Phân loại Playlist</span>
                        <span className="text-xs font-semibold text-slate-300 mt-0.5 block uppercase">
                          {selectedCombo.playlist}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic mt-8 text-center">
                      Chọn một hàng bên bảng danh sách để xem chi tiết đòn đánh hoặc nhấn "Create New".
                    </p>
                  )}
                </div>

                {selectedCombo && (
                  <div className="p-3.5 bg-slate-900/60 rounded-xl border border-slate-800 mt-6 flex flex-col gap-1.5 text-[10px] leading-relaxed text-slate-400 shrink-0">
                    <span className="text-[10px] font-bold text-cyan-400/90 font-mono"># PYTHON ACTION API:</span>
                    <span className="font-mono text-[9px] break-all">
                      POST /api/select_combo<br />
                      body: {JSON.stringify(selectedCombo)}
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>

        </div>

      </div>

      {/* Action logs notifications status */}
      {actionStatus && (
        <div className={`absolute bottom-24 right-8 px-4 py-3 rounded-xl border text-xs font-bold flex items-center gap-2 animate-bounce shadow-xl ${
          actionStatus === 'saving' || actionStatus === 'deleting' || actionStatus === 'playing' ? 'bg-slate-900 border-cyan-500/30 text-cyan-400' :
          actionStatus.startsWith('success') ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-400 shadow-emerald-900/10' :
          'bg-slate-900 border-slate-800 text-slate-400'
        }`}>
          {(actionStatus === 'saving' || actionStatus === 'deleting' || actionStatus === 'playing') && <div className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />}
          {actionStatus.startsWith('success') && <CheckCircle className="w-4 h-4 text-emerald-400" />}
          {actionStatus === 'playing' && 'Đang gửi tín hiệu kích hoạt combo...'}
          {actionStatus === 'success_play' && `Đã kích hoạt: "${selectedCombo?.name}" thành công!`}
          {actionStatus === 'saving' && 'Đang lưu chỉnh sửa...'}
          {actionStatus === 'success_save' && 'Đã lưu cấu hình list thành công!'}
          {actionStatus === 'deleting' && 'Đang xoá combo khỏi list...'}
          {actionStatus === 'success_delete' && 'Đã xoá combo khỏi list thành công!'}
        </div>
      )}

      {/* Footer bar spacing */}
      <div className="h-2 shrink-0" />
    </div>
  );
};

export default ComboListPanel;
