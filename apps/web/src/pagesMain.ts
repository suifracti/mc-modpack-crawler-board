import './desktopShell-v2.css';
import './pages.css';
import { installPagesApi } from './pagesApi';
import { initDesktopShellV2 } from './desktopShell-v2';
installPagesApi();
document.documentElement.dataset.uiVersion = 'v2';
void initDesktopShellV2();

document.addEventListener('keydown', event => {
  if (!(event.ctrlKey || event.metaKey) || event.altKey || event.key.toLowerCase() !== 'k') return;
  const search = document.querySelector<HTMLInputElement>('#pack-search');
  if (!search) return;
  event.preventDefault();
  search.focus();
  search.select();
});
