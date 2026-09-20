const { contextBridge, ipcRenderer } = require('electron');

function subscribe(channel, callback) {
  const listener = (_event, payload) => callback(payload);
  ipcRenderer.on(channel, listener);
  return () => ipcRenderer.removeListener(channel, listener);
}

contextBridge.exposeInMainWorld('desktopApi', Object.freeze({
  getState: () => ipcRenderer.invoke('desktop:get-state'),
  getPlatformRecords: (platform, query = '') => ipcRenderer.invoke('desktop:get-platform-records', platform, query),
  chooseDataDirectory: () => ipcRenderer.invoke('desktop:choose-data-directory'),
  startUpdate: (platform, options = {}) => ipcRenderer.invoke('desktop:start-update', platform, options),
  cancelUpdate: () => ipcRenderer.invoke('desktop:cancel-update'),
  openExternal: (url) => ipcRenderer.invoke('desktop:open-external', url),
  onUpdateStatus: (callback) => subscribe('desktop:update-status', callback),
  onUpdateLog: (callback) => subscribe('desktop:update-log', callback),
  onDataChanged: (callback) => subscribe('desktop:data-changed', callback),
}));
