const { app, BrowserWindow, dialog, ipcMain, shell, session } = require('electron');
const fs = require('node:fs');
const fsp = require('node:fs/promises');
const path = require('node:path');
const { DataStore, defaultUserDataRoot } = require('./lib/data-store.cjs');
const { PLATFORM_CONFIGS, assertPlatform, isHttpUrl } = require('./lib/platforms.cjs');
const { UpdateManager } = require('./lib/update-manager.cjs');
const { createProcessRunner } = require('./lib/process-runner.cjs');
const { getPreviewVersions } = require('./lib/preview-versions.cjs');

const isPackaged = app.isPackaged;
const repoRoot = path.resolve(__dirname, '..', '..');
const resourceRoot = isPackaged ? process.resourcesPath : repoRoot;
const dataRoot = path.resolve(process.env.MC_DESKTOP_DATA_ROOT || defaultUserDataRoot());
const store = new DataStore(dataRoot);
let mainWindow = null;
let quitting = false;

function frontendPath() {
  return isPackaged
    ? path.join(process.resourcesPath, 'frontend', 'desktop.html')
    : path.join(repoRoot, 'build', 'desktop', 'frontend', 'desktop.html');
}

function sourceRoot() {
  return isPackaged ? path.join(process.resourcesPath, 'source') : repoRoot;
}

function pythonCommand() {
  if (process.env.MC_DESKTOP_PYTHON) return process.env.MC_DESKTOP_PYTHON;
  if (isPackaged) {
    const embedded = path.join(process.resourcesPath, 'runtime', process.platform === 'win32' ? 'python.exe' : 'python');
    if (!fs.existsSync(embedded)) throw new Error('应用内置 Python runtime 未找到，请重新安装应用包');
    return embedded;
  }
  return process.platform === 'win32' ? 'python' : 'python3';
}

function workerScript() {
  return isPackaged
    ? path.join(process.resourcesPath, 'runtime', 'collector_worker.py')
    : path.join(repoRoot, 'apps', 'desktop', 'collector_worker.py');
}

function makeRunner({ platform, options, workspace, onLine }) {
  const command = pythonCommand();
  const script = workerScript();
  if (!fs.existsSync(script)) throw new Error(`采集 worker 未找到: ${script}`);
  const args = [script, '--platform', platform, '--workspace', workspace, '--source-root', sourceRoot()];
  if (options.mode) args.push('--mode', String(options.mode));
  if (options.limit) args.push('--limit', String(options.limit));
  if (options.coverOffset !== undefined && options.coverOffset !== null) args.push('--cover-offset', String(options.coverOffset));
  if (options.pages) args.push('--pages', String(options.pages));
  if (options.until) args.push('--until', options.until);
  return createProcessRunner({ command, args, cwd: workspace, onLine });
}

const updateManager = new UpdateManager({
  store,
  runnerFactory: makeRunner,
  logger: (line) => {
    const logPath = path.join(path.dirname(dataRoot), 'logs', 'updates.log');
    fsp.mkdir(path.dirname(logPath), { recursive: true })
      .then(() => fsp.appendFile(logPath, `${new Date().toISOString()} ${line}\n`, 'utf8'))
      .catch(() => {});
  },
});

function broadcast(channel, payload) {
  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send(channel, payload);
}

updateManager.on('status', (status) => broadcast('desktop:update-status', status));
updateManager.on('log', (line) => broadcast('desktop:update-log', line));

function assertSender(event) {
  if (!mainWindow || event.sender !== mainWindow.webContents) throw new Error('非法 IPC 来源');
}

function registerIpc() {
  ipcMain.handle('desktop:preview-versions', (event, platform, sourceId) => {
    assertSender(event);
    return getPreviewVersions(platform, sourceId);
  });
  ipcMain.handle('desktop:get-state', async (event) => {
    assertSender(event);
    return { data: await store.getState(), update: updateManager.getStatus() };
  });
  ipcMain.handle('desktop:get-platform-records', async (event, platform, query) => {
    assertSender(event);
    assertPlatform(platform);
    return store.getPlatformRecords(platform, query);
  });
  ipcMain.handle('desktop:get-platform-comments', async (event, platform, sourceId) => {
    assertSender(event);
    assertPlatform(platform);
    return store.getPlatformComments(platform, sourceId);
  });
  ipcMain.handle('desktop:get-data-library', async (event) => {
    assertSender(event);
    return store.listSnapshots();
  });
  ipcMain.handle('desktop:choose-data-directory', async (event) => {
    assertSender(event);
    const result = await dialog.showOpenDialog(mainWindow, {
      title: '选择已有看板数据目录',
      properties: ['openDirectory'],
      message: '可选择 converted_output、build/frontend_preview 或其中的 data 目录。',
    });
    if (result.canceled || !result.filePaths[0]) return { cancelled: true };
    const data = await store.importDirectory(result.filePaths[0]);
    broadcast('desktop:data-changed', data);
    return { cancelled: false, data };
  });
  ipcMain.handle('desktop:activate-data-snapshot', async (event, snapshotId) => {
    assertSender(event);
    const data = await store.activateSnapshot(snapshotId);
    broadcast('desktop:data-changed', data);
    return { data };
  });
  ipcMain.handle('desktop:delete-data-snapshot', async (event, snapshotId) => {
    assertSender(event);
    const archived = await store.archiveSnapshot(snapshotId);
    return { archived, library: await store.listSnapshots() };
  });
  ipcMain.handle('desktop:export-active-data', async (event) => {
    assertSender(event);
    return store.exportActiveSnapshot();
  });
  ipcMain.handle('desktop:open-data-directory', async (event, snapshotId) => {
    assertSender(event);
    const target = snapshotId ? await store.getSnapshotDirectory(snapshotId) : dataRoot;
    await fsp.mkdir(target, { recursive: true });
    const error = await shell.openPath(target);
    if (error) throw new Error(error);
    return { opened: true, path: target };
  });
  ipcMain.handle('desktop:start-update', async (event, platform, options) => {
    assertSender(event);
    assertPlatform(platform);
    return updateManager.start(platform, options || {});
  });
  ipcMain.handle('desktop:cancel-update', async (event) => {
    assertSender(event);
    return updateManager.cancel();
  });
  ipcMain.handle('desktop:open-external', async (event, url) => {
    assertSender(event);
    if (!isHttpUrl(url)) throw new Error('只允许打开 http/https 原站链接');
    await shell.openExternal(url);
    return { opened: true };
  });
  ipcMain.handle('desktop:flush-session', async (event) => {
    assertSender(event);
    await session.defaultSession.cookies.flushStore().catch(() => {});
    return { ok: true };
  });
  ipcMain.handle('desktop:open-in-app-window', async (event, url, title) => {
    assertSender(event);
    if (!isHttpUrl(url)) throw new Error('只允许打开 http/https 原站链接');
    let subWin = new BrowserWindow({
      parent: mainWindow,
      width: 1160,
      height: 840,
      minWidth: 800,
      minHeight: 600,
      title: title || '原站小窗',
      backgroundColor: '#101722',
      autoHideMenuBar: true,
      webPreferences: {
        session: session.defaultSession,
        nodeIntegration: false,
        contextIsolation: true,
      },
    });
    subWin.loadURL(url);
    subWin.on('closed', () => {
      subWin = null;
      session.defaultSession.cookies.flushStore().catch(() => {});
    });
    return { opened: true };
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1080,
    minHeight: 700,
    title: '我的世界整合包工作台',
    backgroundColor: '#101722',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
      webSecurity: true,
    },
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (isHttpUrl(url)) shell.openExternal(url);
    return { action: 'deny' };
  });
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith('file://')) event.preventDefault();
  });
  await mainWindow.loadFile(frontendPath());
}

app.whenReady().then(async () => {
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    const responseHeaders = { ...details.responseHeaders };
    delete responseHeaders['x-frame-options'];
    delete responseHeaders['X-Frame-Options'];
    delete responseHeaders['content-security-policy'];
    delete responseHeaders['Content-Security-Policy'];
    delete responseHeaders['content-security-policy-report-only'];

    // Ensure Set-Cookie is adapted for embedded in-app window browsing session persistence
    const setCookies = responseHeaders['set-cookie'] || responseHeaders['Set-Cookie'];
    if (setCookies && Array.isArray(setCookies)) {
      responseHeaders['Set-Cookie'] = setCookies.map((cookie) => {
        let modified = cookie;
        if (/;\s*SameSite=(Strict|Lax)/i.test(modified)) {
          modified = modified.replace(/;\s*SameSite=(Strict|Lax)/gi, '; SameSite=None; Secure');
        } else if (!/;\s*SameSite=/i.test(modified)) {
          modified = `${modified}; SameSite=None; Secure`;
        }
        return modified;
      });
    }

    callback({ cancel: false, responseHeaders });
  });

  // Automatically flush cookies to disk when modified
  let flushTimer = null;
  session.defaultSession.cookies.on('changed', () => {
    if (flushTimer) clearTimeout(flushTimer);
    flushTimer = setTimeout(() => {
      session.defaultSession.cookies.flushStore().catch(() => {});
    }, 1500);
  });

  await store.init();
  registerIpc();
  await createWindow();
  app.on('activate', async () => {
    if (BrowserWindow.getAllWindows().length === 0) await createWindow();
  });
});

app.on('before-quit', (event) => {
  session.defaultSession.cookies.flushStore().catch(() => {});
  if (quitting) return;
  if (updateManager.getStatus().state === 'running') {
    event.preventDefault();
    quitting = true;
    updateManager.shutdown().finally(() => app.quit());
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

module.exports = { frontendPath, sourceRoot, pythonCommand };
