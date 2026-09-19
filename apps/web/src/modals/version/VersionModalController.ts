/**
 * Version Modal Controller (Architecture V2 — Phase 3C).
 * Manages modal lifecycle, DOM rendering, tab transitions, and keyboard/click bindings.
 */
import type { VersionModalViewModel } from './types';
import {
  renderOverviewPane,
  renderChangelogPane,
  renderDownloadsPane,
  renderDiscussionsPane,
} from './render';
import { fmtBigNum } from '../../utils/format';
import { recordModalDebug } from '../../debug';

export class VersionModalController {
  private currentVm: VersionModalViewModel | null = null;
  private isBound: boolean = false;

  public getCurrentViewModel(): VersionModalViewModel | null {
    return this.currentVm;
  }

  public init(): void {
    if (this.isBound || typeof document === 'undefined') return;
    this.isBound = true;
    this.bindEvents();
  }

  public open(vm: VersionModalViewModel): void {
    this.init();
    this.currentVm = vm;

    if (typeof window !== 'undefined') {
      recordModalDebug(vm.platform, vm);
    }

    const overlay = document.getElementById('versionModalOverlay');
    if (!overlay) return;

    // 1. Header elements (supporting both versionModal* and vModal* IDs)
    const titleEl = document.getElementById('versionModalTitle');
    const platBadgeEl = document.getElementById('versionModalPlatBadge');
    const verEl = document.getElementById('versionModalVer') || document.getElementById('vModalVer');
    const dateEl = document.getElementById('versionModalDate') || document.getElementById('vModalDate');
    const countEl = document.getElementById('versionModalCount') || document.getElementById('vModalCount');
    const extLinkEl = (document.getElementById('versionModalExtLink') ||
      document.getElementById('vModalExtLink')) as HTMLAnchorElement | null;

    if (titleEl) titleEl.textContent = `${vm.title} · ${vm.platformName}`;
    if (platBadgeEl) platBadgeEl.textContent = `📜 ${vm.platformName}`;
    if (verEl) verEl.textContent = `最新版本: ${vm.latestVersion}`;
    if (dateEl) dateEl.textContent = `更新时间: ${vm.lastUpdated}`;
    if (countEl) {
      const cntStr = vm.versionCount ? fmtBigNum(vm.versionCount) : '1';
      countEl.textContent = `累计发布: ${cntStr} 个版本`;
    }
    if (extLinkEl) extLinkEl.href = vm.targetUrl;

    // 2. Badges
    const badgeChangelog = document.getElementById('vBadgeChangelog');
    const badgeDownloads = document.getElementById('vBadgeDownloads');
    const badgeDiscussions = document.getElementById('vBadgeDiscussions');

    const totalFiles = (vm.releases || []).reduce(
      (acc, r) => acc + (r.downloads?.length || 1),
      0
    );

    if (badgeChangelog) badgeChangelog.textContent = String(vm.releases?.length || 0);
    if (badgeDownloads) badgeDownloads.textContent = String(totalFiles);
    if (badgeDiscussions) badgeDiscussions.textContent = '1';

    // 3. Panes
    const pOverview = document.getElementById('vPaneOverview');
    const pChangelog = document.getElementById('vPaneChangelog');
    const pDownloads = document.getElementById('vPaneDownloads');
    const pDiscussions = document.getElementById('vPaneDiscussions');

    if (pOverview) pOverview.innerHTML = renderOverviewPane(vm);
    if (pChangelog) pChangelog.innerHTML = renderChangelogPane(vm);
    if (pDownloads) pDownloads.innerHTML = renderDownloadsPane(vm);
    if (pDiscussions) pDiscussions.innerHTML = renderDiscussionsPane(vm);

    // 4. Default to Overview or Changelog tab
    this.switchTab('overview');

    // 5. Show overlay
    overlay.style.display = 'flex';
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  public close(): void {
    const overlay = document.getElementById('versionModalOverlay');
    if (overlay) {
      overlay.classList.remove('show');
      overlay.style.display = 'none';
    }
    document.body.style.overflow = '';
    this.currentVm = null;
  }

  public switchTab(tabId: 'overview' | 'changelog' | 'downloads' | 'discussions'): void {
    // Switch active class on tab buttons
    const tabBtns = document.querySelectorAll('.vmodal-tab-btn, .version-tab-btn');
    tabBtns.forEach((btn) => {
      const target = btn.getAttribute('data-vtab') || btn.getAttribute('data-tab');
      if (target === tabId) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    // Switch pane visibility
    const panes = document.querySelectorAll('.vmodal-pane, .version-pane');
    panes.forEach((pane) => {
      const pid = pane.id;
      if (
        (tabId === 'overview' && pid === 'vPaneOverview') ||
        (tabId === 'changelog' && pid === 'vPaneChangelog') ||
        (tabId === 'downloads' && pid === 'vPaneDownloads') ||
        (tabId === 'discussions' && pid === 'vPaneDiscussions')
      ) {
        pane.classList.add('active');
        (pane as HTMLElement).style.display = 'block';
      } else {
        pane.classList.remove('active');
        (pane as HTMLElement).style.display = 'none';
      }
    });
  }

  private bindEvents(): void {
    // Close button & tab clicks
    document.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      if (
        target &&
        (target.id === 'versionModalClose' ||
          target.id === 'versionModalCloseBtn' ||
          target.classList.contains('close') ||
          target.closest('#versionModalClose') ||
          target.closest('#versionModalCloseBtn') ||
          target.closest('.version-modal-close-btn') ||
          target.closest('.close'))
      ) {
        e.preventDefault();
        this.close();
      } else if (target && target.id === 'versionModalOverlay') {
        this.close();
      } else if (
        target &&
        (target.classList.contains('vmodal-tab-btn') || target.classList.contains('version-tab-btn'))
      ) {
        const tab = (target.getAttribute('data-vtab') || target.getAttribute('data-tab')) as
          | 'overview'
          | 'changelog'
          | 'downloads'
          | 'discussions'
          | null;
        if (tab) {
          e.preventDefault();
          this.switchTab(tab);
        }
      }
    });

    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const overlay = document.getElementById('versionModalOverlay');
        if (overlay && overlay.style.display !== 'none') {
          this.close();
        }
      }
    });
  }
}

export const versionModalController = new VersionModalController();
