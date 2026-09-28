const { contextBridge, ipcRenderer } = require('electron');

function subscribe(channel, callback) {
  const listener = (_event, payload) => callback(payload);
  ipcRenderer.on(channel, listener);
  return () => ipcRenderer.removeListener(channel, listener);
}

contextBridge.exposeInMainWorld('desktopApi', Object.freeze({
  nativeDataDirectoryPicker: true,
  getPreviewVersions: (platform, sourceId) => ipcRenderer.invoke('desktop:preview-versions', platform, sourceId),
  getState: () => ipcRenderer.invoke('desktop:get-state'),
  getPlatformRecords: (platform, query = '') => ipcRenderer.invoke('desktop:get-platform-records', platform, query),
  getPlatformComments: (platform, sourceId) => ipcRenderer.invoke('desktop:get-platform-comments', platform, sourceId),
  getDataLibrary: () => ipcRenderer.invoke('desktop:get-data-library'),
  chooseDataDirectory: () => ipcRenderer.invoke('desktop:choose-data-directory'),
  activateDataSnapshot: (snapshotId) => ipcRenderer.invoke('desktop:activate-data-snapshot', snapshotId),
  deleteDataSnapshot: (snapshotId) => ipcRenderer.invoke('desktop:delete-data-snapshot', snapshotId),
  exportActiveData: () => ipcRenderer.invoke('desktop:export-active-data'),
  openDataDirectory: (snapshotId) => ipcRenderer.invoke('desktop:open-data-directory', snapshotId),
  startUpdate: (platform, options = {}) => ipcRenderer.invoke('desktop:start-update', platform, options),
  cancelUpdate: () => ipcRenderer.invoke('desktop:cancel-update'),
  openExternal: (url) => ipcRenderer.invoke('desktop:open-external', url),
  openInAppWindow: (url, title) => ipcRenderer.invoke('desktop:open-in-app-window', url, title),
  flushSession: () => ipcRenderer.invoke('desktop:flush-session'),
  onUpdateStatus: (callback) => subscribe('desktop:update-status', callback),
  onUpdateLog: (callback) => subscribe('desktop:update-log', callback),
  onDataChanged: (callback) => subscribe('desktop:data-changed', callback),
}));
