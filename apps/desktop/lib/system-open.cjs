const { spawn } = require('node:child_process');

const WINDOWS_OPEN_DIRECTORY_SCRIPT = [
  '$target = [System.IO.Path]::GetFullPath($env:MC_OPEN_TARGET)',
  '$shell = New-Object -ComObject Shell.Application',
  '$find = { @($shell.Windows() | Where-Object { try { $_.Document.Folder.Self.Path -eq $target } catch { $false } }) }',
  '$windows = & $find',
  'if (-not $windows.Count) { Start-Process -FilePath $target; Start-Sleep -Milliseconds 450; $windows = & $find }',
  'if (-not $windows.Count) { throw "Explorer did not expose the requested directory window" }',
  '$activator = New-Object -ComObject WScript.Shell',
  '$null = $activator.AppActivate([string]$windows[-1].LocationName)',
].join('; ');

function openCommand(target, { platform = process.platform, kind = 'path' } = {}) {
  if (platform === 'win32') {
    return kind === 'url'
      ? { command: 'rundll32.exe', args: ['url.dll,FileProtocolHandler', target], windowsHide: true }
      : {
        command: 'powershell.exe',
        args: ['-NoProfile', '-STA', '-NonInteractive', '-Command', WINDOWS_OPEN_DIRECTORY_SCRIPT],
        windowsHide: true,
        env: { MC_OPEN_TARGET: target },
      };
  }
  if (platform === 'darwin') return { command: 'open', args: [target], windowsHide: false };
  return { command: 'xdg-open', args: [target], windowsHide: false };
}

function openSystemTarget(target, options = {}) {
  const launch = openCommand(target, options);
  return new Promise((resolve, reject) => {
    const child = spawn(launch.command, launch.args, {
      detached: false,
      stdio: 'ignore',
      windowsHide: launch.windowsHide,
      env: { ...process.env, ...(launch.env || {}) },
    });
    child.once('error', reject);
    child.once('close', (code, signal) => {
      if (code === 0) resolve({ opened: true, target });
      else reject(new Error(`系统打开命令失败（${signal || `exit ${code}`}）`));
    });
  });
}

module.exports = { openCommand, openSystemTarget };
