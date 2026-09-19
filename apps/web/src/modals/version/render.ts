/**
 * Version Modal Renderers (Architecture V2 — Phase 3C).
 * Pure HTML rendering functions for Version Modal Header, Overview, Changelog, Downloads, and Discussions.
 */
import { escHtml } from '../../utils/html';
import { fmtBigNum } from '../../utils/format';
import type { VersionModalViewModel } from './types';

export function buildMcVersionStrip(versions: string[]): string {
  if (!versions || !versions.length) return '';
  const uniq: string[] = [];
  versions.forEach((v) => {
    const s = String(v == null ? '' : v).trim();
    if (s && !uniq.includes(s)) uniq.push(s);
  });
  if (uniq.length < 2) return '';

  const fam: Record<string, string[]> = {};
  const order: string[] = [];
  uniq.forEach((v) => {
    const m = v.match(/^(\d+\.\d+)/);
    const key = m ? m[1] : '其它';
    if (!fam[key]) {
      fam[key] = [];
      order.push(key);
    }
    fam[key].push(v);
  });

  order.sort((a, b) => {
    const pa = a.split('.');
    const pb = b.split('.');
    return (
      (parseInt(pb[0], 10) || 0) - (parseInt(pa[0], 10) || 0) ||
      (parseInt(pb[1], 10) || 0) - (parseInt(pa[1], 10) || 0)
    );
  });

  let maxN = 1;
  order.forEach((k) => {
    maxN = Math.max(maxN, fam[k].length);
  });

  const rows = order
    .map((k) => {
      const n = fam[k].length;
      const pct = Math.max(6, Math.round((n / maxN) * 100));
      return (
        '<div class="mcver-row" title="' +
        escHtml(fam[k].join(', '), true) +
        '">' +
        '<span class="mcver-fam">' +
        escHtml(k) +
        '</span>' +
        '<span class="mcver-track"><span class="mcver-fill" style="width:' +
        pct +
        '%;"></span></span>' +
        '<span class="mcver-n">' +
        n +
        ' 个</span>' +
        '</div>'
      );
    })
    .join('');

  return (
    '<div class="mcver-strip">' +
    '<div class="mcver-head">🎮 Minecraft 版本支持分布' +
    '<span class="mcver-sub">共 ' +
    uniq.length +
    ' 个具体版本 · 按大版本族聚合 · 悬停可看明细</span>' +
    '</div>' +
    rows +
    '</div>'
  );
}

export function renderSimpleMarkdown(md: string): string {
  if (!md) return '';
  let text = String(md);
  const escapeMap: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  };
  text = text.replace(/[&<>"']/g, (s) => escapeMap[s] || s);

  text = text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (_m, _lang, code) => {
    return (
      '<pre class="vmodal-code-block" style="background:var(--bg-surface); padding:10px 14px; border-radius:6px; overflow-x:auto; font-size:0.82rem; border:1px solid var(--border-subtle); margin:8px 0;"><code>' +
      code.trim() +
      '</code></pre>'
    );
  });

  text = text.replace(
    /`([^`]+)`/g,
    '<code style="background:var(--bg-surface); padding:1px 5px; border-radius:4px; font-size:0.82rem; color:var(--accent-amber);">$1</code>'
  );

  text = text.replace(
    /^#### (.*?)$/gm,
    '<h4 style="font-size:0.95rem; font-weight:700; margin:10px 0 4px; color:var(--accent-primary);">$1</h4>'
  );
  text = text.replace(
    /^### (.*?)$/gm,
    '<h3 style="font-size:1.02rem; font-weight:700; margin:12px 0 6px; color:var(--accent-primary);">$1</h3>'
  );
  text = text.replace(
    /^## (.*?)$/gm,
    '<h2 style="font-size:1.1rem; font-weight:700; margin:14px 0 8px; color:var(--accent-primary);">$1</h2>'
  );
  text = text.replace(
    /^# (.*?)$/gm,
    '<h1 style="font-size:1.2rem; font-weight:700; margin:16px 0 10px; color:var(--accent-primary);">$1</h1>'
  );

  text = text.replace(
    /^> (.*?)$/gm,
    '<blockquote style="border-left:3px solid var(--accent-primary); padding-left:10px; margin:6px 0; color:var(--text-muted); font-style:italic;">$1</blockquote>'
  );

  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/__([^_]+)__/g, '<strong>$1</strong>');
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  text = text.replace(/_([^_]+)_/g, '<em>$1</em>');
  text = text.replace(/~~([^~]+)~~/g, '<del>$1</del>');

  text = text.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g,
    '<a href="$2" target="_blank" rel="noreferrer" style="color:var(--accent-primary); text-decoration:underline;">$1 ↗</a>'
  );

  text = text.replace(/^\s*[-*+]\s+(.*?)$/gm, '<li style="margin-bottom:3px;">$1</li>');
  text = text.replace(
    /(<li style="margin-bottom:3px;">.*<\/li>(\n|$))+/g,
    '<ul style="padding-left:20px; margin:6px 0;">$&</ul>'
  );

  text = text.replace(/^\s*\d+\.\s+(.*?)$/gm, '<li class="vmodal-oli" style="margin-bottom:3px;">$1</li>');
  text = text.replace(
    /(<li class="vmodal-oli" style="margin-bottom:3px;">.*<\/li>(\n|$))+/g,
    '<ol style="padding-left:20px; margin:6px 0;">$&</ol>'
  );

  const lines = text.split('\n');
  const res: string[] = [];
  for (let i = 0; i < lines.length; i++) {
    const l = lines[i];
    if (/^<(h[1-4]|ul|ol|pre|blockquote|\/ul|\/ol|\/pre|\/blockquote)/.test(l.trim())) {
      res.push(l);
    } else if (l.trim() === '') {
      res.push('<div style="height:6px;"></div>');
    } else {
      res.push('<p style="margin:3px 0; line-height:1.6;">' + l + '</p>');
    }
  }
  return res.join('\n');
}

export function renderOverviewPane(vm: VersionModalViewModel): string {
  let formerTitlesHtml = '';
  if (vm.formerTitles && vm.formerTitles.length > 0) {
    formerTitlesHtml =
      '<div style="background:rgba(245,158,11,0.08); border-left:4px solid var(--accent-amber); padding:10px 14px; border-radius:0 8px 8px 0; margin-bottom:16px; font-size:0.86rem; color:var(--text-primary);">' +
      '<b>🏷️ 该整合包曾用名（历史别名）：</b> ' +
      escHtml(vm.formerTitles.join('、 ')) +
      '<span style="font-size:0.75rem; color:var(--text-muted); margin-left:8px;">(全局搜索旧名称依然可精准命中)</span>' +
      '</div>';
  }

  let envPillText = vm.envDisplay;
  if (!envPillText) {
    if (vm.serverStatus === 'unsupported') {
      envPillText = '明确不支持开服 / 仅客户端运行';
    } else if (vm.hasServer || vm.serverStatus === 'supported' || vm.serverStatus === 'required' || vm.serverStatus === 'optional') {
      envPillText = '支持联机开服 / 提供专用服务端';
    } else {
      envPillText = '未声明服务端支持 / 无法确认';
    }
  }

  const envBoxHtml =
    '<div class="vmodal-env-box">' +
    '<div class="vmodal-env-label">⚙️ 运行环境支持 (Runtime Environment)</div>' +
    '<div class="vmodal-env-pills">' +
    '<span class="vmodal-env-pill active">🖵 客户端 (支持单人游玩/客户端运行)</span>' +
    '<span class="vmodal-env-pill ' +
    (vm.hasServer ? 'active active-server' : '') +
    '">🖳 服务端 (' +
    escHtml(envPillText) +
    ')</span>' +
    '</div>' +
    '</div>';

  let groupVerHtml = '';
  if (vm.hasGroupVersion) {
    groupVerHtml =
      '<div class="bili-group-ver-banner" style="margin-bottom:16px; font-size:0.92rem; padding:12px 16px;">' +
      '👥 <strong>群内有最新版本提示</strong>：' +
      escHtml(
        vm.groupVersionNote ||
          'UP主在简介/置顶评论中提示最新版本仅在QQ群内发布，请加入QQ群获取体验！'
      ) +
      (vm.qqGroup ? ' (QQ群号: <b>' + escHtml(vm.qqGroup) + '</b>)' : '') +
      '</div>';
  }

  const mcStrip = buildMcVersionStrip(vm.mcVersionsList);

  const noticeText =
    vm.noticeText ||
    '为保障您的本地数据浏览安全，防止 ' +
      vm.siteShort +
      ' 原站防爬拦截误封您的 IP（以及规避原网页防内嵌劫持脚本导致整个看板跳转），本弹窗已直接利用本地聚合数据库为您秒级呈现版本元信息。如需查阅官方历史每一个微小版本的详细改动日志，可点击下方按钮在新独立标签页中安全访问。';

  const btnLabel = vm.btnLabel || '在新标签页打开 ' + vm.siteShort + ' 官方页面 ↗';

  return (
    formerTitlesHtml +
    groupVerHtml +
    envBoxHtml +
    '<div class="version-details-grid" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:14px; margin-bottom:18px;">' +
    '<div class="vcard-metric" style="background:var(--bg-surface-elevated); border:1px solid var(--border-subtle); border-radius:12px; padding:14px;">' +
    '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">🏷️ 最新发布版本</div>' +
    '<div style="font-size:1.15rem; font-weight:700; color:var(--accent-primary);">' +
    escHtml(vm.latestVersion) +
    '</div>' +
    '</div>' +
    '<div class="vcard-metric" style="background:var(--bg-surface-elevated); border:1px solid var(--border-subtle); border-radius:12px; padding:14px;">' +
    '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">📅 最近更新时间</div>' +
    '<div style="font-size:1.05rem; font-weight:700; color:var(--text-primary);">' +
    escHtml(vm.lastUpdated) +
    '</div>' +
    '</div>' +
    '<div class="vcard-metric" style="background:var(--bg-surface-elevated); border:1px solid var(--border-subtle); border-radius:12px; padding:14px;">' +
    '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">🚀 首次发布日期</div>' +
    '<div style="font-size:1.05rem; font-weight:700; color:var(--text-primary);">' +
    escHtml(vm.dateCreated || vm.lastUpdated) +
    '</div>' +
    '</div>' +
    '<div class="vcard-metric" style="background:var(--bg-surface-elevated); border:1px solid var(--border-subtle); border-radius:12px; padding:14px;">' +
    '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">📦 累计历史版本数</div>' +
    '<div style="font-size:1.15rem; font-weight:700; color:var(--accent-secondary, #8b5cf6);">' +
    (vm.versionCount ? fmtBigNum(vm.versionCount) + ' 个版本' : '未知') +
    '</div>' +
    '</div>' +
    '<div class="vcard-metric" style="background:var(--bg-surface-elevated); border:1px solid var(--border-subtle); border-radius:12px; padding:14px;">' +
    '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">🎮 Minecraft 支持版本</div>' +
    '<div style="font-size:1.02rem; font-weight:700; color:var(--emerald, #059669);">' +
    (mcStrip ? vm.mcVersionsList.length + ' 个具体版本' : escHtml(vm.mcVersionsSummary)) +
    '</div>' +
    '</div>' +
    '<div class="vcard-metric" style="background:var(--bg-surface-elevated); border:1px solid var(--border-subtle); border-radius:12px; padding:14px;">' +
    '<div style="font-size:0.75rem; color:var(--text-muted); margin-bottom:4px;">🧩 整合包类型与模组量</div>' +
    '<div style="font-size:1.02rem; font-weight:700; color:var(--text-primary);">' +
    escHtml(vm.typeName) +
    (vm.modCountStr ? ' · ' + escHtml(vm.modCountStr) : '') +
    '</div>' +
    '</div>' +
    '</div>' +
    mcStrip +
    '<div class="vcard-notice" style="background:rgba(37,99,235,0.08); border-left:4px solid var(--primary); padding:14px 18px; border-radius:0 10px 10px 0; margin-bottom:20px; font-size:0.86rem; line-height:1.6; color:var(--text-primary);">' +
    '<b>🛡️ 本地离线安全保护说明：</b><br>' +
    noticeText +
    '</div>' +
    '<div style="text-align:center; padding:12px 0;">' +
    '<a href="' +
    vm.targetUrl +
    '" target="_blank" rel="noopener noreferrer" class="btn btn-primary" style="display:inline-flex; align-items:center; gap:8px; padding:9px 22px; font-size:0.92rem; font-weight:700; border-radius:8px; text-decoration:none;">' +
    '<span>' +
    escHtml(btnLabel) +
    '</span>' +
    '</a>' +
    '</div>'
  );
}

export function renderChangelogPane(vm: VersionModalViewModel): string {
  const releases = vm.releases || [];
  if (releases.length === 0) {
    return '<div class="vmodal-ver-card" style="text-align:center; padding:30px; color:var(--text-muted);">暂无版本日志数据</div>';
  }

  let html = '<div class="vmodal-changelog-timeline">';
  releases.forEach((rel) => {
    const vNum = rel.versionName || rel.versionId || '未知版本';
    const vDate = rel.date ? String(rel.date).substring(0, 10) : '未知日期';
    const gvStr = rel.gameVersions?.length ? `MC ${rel.gameVersions.join(', ')}` : '';
    const ldStr = rel.loaders?.length ? rel.loaders.join(', ') : '';

    let filesBtnHtml = '';
    if (rel.downloads && rel.downloads.length > 0) {
      filesBtnHtml += '<div style="margin-top:12px; display:flex; flex-wrap:wrap; gap:8px;">';
      rel.downloads.forEach((dl) => {
        const panCls = dl.panClass || 'pan-btn-other';
        const label = dl.name || '下载整合包';
        const size = dl.sizeStr ? ` (${dl.sizeStr})` : '';
        const code = dl.code ? ` 提取码: ${dl.code}` : '';
        filesBtnHtml += `<a href="${dl.url}" target="_blank" rel="noreferrer" class="card-dl-btn ${panCls}" style="font-size:0.78rem; padding:4px 10px;" title="${escHtml(label + code, true)}">💾 ${escHtml(label)}${size} ↗</a>`;
      });
      filesBtnHtml += '</div>';
    }

    const changelogBody = rel.changelogHtml
      ? rel.changelogHtml
      : renderSimpleMarkdown(rel.changelogMd || '该版本未提供更新日志说明。');

    html +=
      '<div class="vmodal-ver-card">' +
      '<div class="vmodal-ver-head">' +
      '<div class="vmodal-ver-title">' +
      '<span class="vmodal-ver-tag">🏷️ ' +
      escHtml(vNum) +
      '</span>' +
      '<span>' +
      escHtml(rel.versionName) +
      '</span>' +
      '</div>' +
      '<div class="vmodal-ver-meta">' +
      '<span>📅 ' +
      escHtml(vDate) +
      '</span>' +
      (gvStr ? '<span>🎮 ' + escHtml(gvStr) + '</span>' : '') +
      (ldStr ? '<span>🧩 ' + escHtml(ldStr) + '</span>' : '') +
      '</div>' +
      '</div>' +
      '<div class="vmodal-changelog-body">' +
      changelogBody +
      '</div>' +
      filesBtnHtml +
      '</div>';
  });
  html += '</div>';
  return html;
}

export function renderDownloadsPane(vm: VersionModalViewModel): string {
  const releases = vm.releases || [];
  let dtHtml =
    '<div class="vmodal-dl-top-bar">' +
    '<div style="font-weight:700; color:var(--text-primary); font-size:0.9rem;">📥 历史发布版本与下载矩阵 (共 ' +
    releases.length +
    ' 个版本)</div>' +
    '<input type="text" class="vmodal-dl-search" placeholder="🔍 快速搜索版本号、MC版本或加载器...">' +
    '</div>' +
    '<div class="vmodal-dl-table-wrap">' +
    '<table class="vmodal-dl-table">' +
    '<thead>' +
    '<tr>' +
    '<th>版本号</th>' +
    '<th>游戏版本</th>' +
    '<th>加载器</th>' +
    '<th>发布日期</th>' +
    '<th>下载量 / 大小</th>' +
    '<th>下载通道 / 操作</th>' +
    '</tr>' +
    '</thead>' +
    '<tbody>';

  releases.forEach((rel) => {
    const vNum = rel.versionName || '--';
    const gvStr = rel.gameVersions?.length ? rel.gameVersions.join(', ') : '--';
    const ldStr = rel.loaders?.length ? rel.loaders.join(', ') : '--';
    const vDate = rel.date ? String(rel.date).substring(0, 10) : '--';
    const firstDl = rel.downloads?.[0];
    const sizeStr = firstDl?.sizeStr || '';

    let opBtns = '';
    if (rel.downloads && rel.downloads.length > 0) {
      rel.downloads.forEach((dl) => {
        const panCls = dl.panClass || 'pan-btn-other';
        const label = dl.name || '极速下载';
        opBtns += `<a href="${dl.url}" target="_blank" rel="noreferrer" class="card-dl-btn ${panCls}" style="font-size:0.75rem; margin-right:4px; margin-bottom:4px;">💾 ${escHtml(label)} ↗</a>`;
      });
    } else {
      opBtns = `<a href="${vm.targetUrl}" target="_blank" rel="noreferrer" class="card-dl-btn pan-btn-other" style="font-size:0.75rem;">🔗 原站下载 ↗</a>`;
    }

    dtHtml +=
      '<tr>' +
      '<td><span class="vmodal-ver-tag">' +
      escHtml(vNum) +
      '</span></td>' +
      '<td>' +
      escHtml(gvStr) +
      '</td>' +
      '<td>' +
      escHtml(ldStr) +
      '</td>' +
      '<td>' +
      escHtml(vDate) +
      '</td>' +
      '<td>' +
      (sizeStr ? '<span style="font-size:0.75rem; color:var(--text-muted);">' + sizeStr + '</span>' : '--') +
      '</td>' +
      '<td>' +
      opBtns +
      '</td>' +
      '</tr>';
  });
  dtHtml += '</tbody></table></div>';
  return dtHtml;
}

export function renderDiscussionsPane(vm: VersionModalViewModel): string {
  if (vm.discussionsHtml) {
    return vm.discussionsHtml;
  }

  return (
    '<div class="vmodal-ver-card">' +
    '<h4 style="margin:0 0 8px; color:var(--text-primary); font-size:1rem;">💬 ' +
    escHtml(vm.platformName) +
    ' 社区讨论与反馈</h4>' +
    '<p style="font-size:0.86rem; color:var(--text-secondary); line-height:1.6; margin-bottom:14px;">' +
    '您可以在 ' +
    escHtml(vm.siteShort) +
    ' 开放平台与整合包创作者及社区玩家直接交流、提交问题反馈或阅读玩家评测。' +
    '</p>' +
    '<a href="' +
    vm.targetUrl +
    '" target="_blank" rel="noreferrer" class="btn btn-primary" style="display:inline-flex; align-items:center; gap:6px; padding:8px 18px; font-weight:700; border-radius:8px; text-decoration:none;">' +
    '<span>在新标签页打开 ' +
    escHtml(vm.siteShort) +
    ' 官方讨论区 ↗</span>' +
    '</a>' +
    '</div>'
  );
}
