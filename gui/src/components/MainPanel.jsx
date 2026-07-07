import React from 'react';
import SettingsPanel from './SettingsPanel';
import Player2InputPanel from './Player2InputPanel';
import ComboCustomPanel from './ComboCustomPanel';
import ComboListPanel from './ComboListPanel';
import SystemLogsPanel from './SystemLogsPanel';

const MainPanel = ({ activeTab }) => {
  // Switch render the correct panel based on current sidebar tab selection
  switch (activeTab) {
    case 1:
      return <SettingsPanel />;
    case 2:
      return <Player2InputPanel />;
    case 3:
      return <ComboCustomPanel />;
    case 4:
      return <ComboListPanel />;
    case 5:
      return <SystemLogsPanel />;
    default:
      return <SettingsPanel />;
  }
};

export default MainPanel;
