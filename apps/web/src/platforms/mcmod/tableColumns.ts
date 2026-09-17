/**
 * MCMod DataTables Column Definitions (Architecture V2 — Phase 3B).
 * Connects DataTables directly to TypeScript renderers without c0~c6.
 */
import {
  renderTitleCell,
  renderTrendCell,
  renderGrowthCell,
  renderVotesCell,
  renderEngageCell,
  renderTagsCell,
  renderModsCell,
} from './renderer';
import type { McmodStructuredItem } from './types';

export function getMcmodTableColumns(): unknown[] {
  return [
    {
      data: null,
      type: 'string',
      orderSequence: ['asc', 'desc'],
      render: (row: McmodStructuredItem, type: string) => {
        if (type === 'sort' || type === 'order') {
          return (row.title || '').toLowerCase();
        }
        if (type === 'filter' || type === 'search') {
          const former = row.formerTitles && row.formerTitles.length ? row.formerTitles.join(' ') : '';
          return `${row.title || ''} ${row.typeName || ''} ${former}`.trim();
        }
        return renderTitleCell(row);
      },
    },
    {
      data: null,
      type: 'num',
      orderSequence: ['desc', 'asc'],
      render: (row: McmodStructuredItem, type: string) => {
        if (type === 'sort' || type === 'order') {
          return row.trendStats?.score || 0;
        }
        return renderTrendCell(row);
      },
    },
    {
      data: null,
      type: 'num',
      orderSequence: ['desc', 'asc'],
      render: (row: McmodStructuredItem, type: string) => {
        if (type === 'sort' || type === 'order') {
          return row.trendStats?.t7 || 0;
        }
        return renderGrowthCell(row);
      },
    },
    {
      data: null,
      type: 'num',
      orderSequence: ['desc', 'asc'],
      render: (row: McmodStructuredItem, type: string) => {
        if (type === 'sort' || type === 'order') {
          return row.votes?.redVotes || 0;
        }
        return renderVotesCell(row);
      },
    },
    {
      data: null,
      type: 'num',
      orderSequence: ['desc', 'asc'],
      render: (row: McmodStructuredItem, type: string) => {
        if (type === 'sort' || type === 'order') {
          return row.commentsCount || 0;
        }
        return renderEngageCell(row);
      },
    },
    {
      data: null,
      type: 'num',
      orderSequence: ['desc', 'asc'],
      render: (row: McmodStructuredItem, type: string) => {
        if (type === 'sort' || type === 'order') {
          return (row.categories || []).length;
        }
        if (type === 'filter' || type === 'search') {
          return (row.categories || []).join(' ');
        }
        return renderTagsCell(row);
      },
    },
    {
      data: null,
      type: 'num',
      orderSequence: ['desc', 'asc'],
      render: (row: McmodStructuredItem, type: string) => {
        if (type === 'sort' || type === 'order') {
          return row.includedModsCount || 0;
        }
        if (type === 'filter' || type === 'search') {
          return row.modSearchText || '';
        }
        return renderModsCell(row);
      },
    },
  ];
}

interface JQChain {
  addClass(c: string): JQChain;
  attr(k: string, v?: unknown): JQChain;
}

interface JQRow {
  attr(k: string, v?: unknown): JQRow;
  children(sel: string): { eq: (n: number) => JQChain };
}

export function attachMcmodRowAttributes(
  row: HTMLElement,
  rowData: McmodStructuredItem,
  dataIndex: number
): void {
  const win = window as unknown as { $: (el: unknown) => JQRow };
  if (!win.$) return;

  const $row = win.$(row);
  $row.attr('data-row', dataIndex);
  $row.attr('data-mid', rowData.mid);

  const $tds = $row.children('td');
  const hasCover = Boolean(rowData.coverUrl);

  $tds.eq(0)
    .addClass('td-title' + (hasCover ? ' has-cover' : ''))
    .attr('data-type-search', rowData.typeName || '')
    .attr('data-name', (rowData.title || '').toLowerCase())
    .attr('data-order', (rowData.title || '').toLowerCase())
    .attr('data-views', rowData.views);

  $tds.eq(1)
    .addClass('td-trend')
    .attr('data-score', rowData.score)
    .attr('data-lat', rowData.trendStats?.lat || 0)
    .attr('data-max', rowData.trendStats?.max || 0)
    .attr('data-avg', rowData.trendStats?.avg || 0)
    .attr('data-days', rowData.trendStats?.days || 0)
    .attr('data-order', rowData.trendStats?.score || 0)
    .attr('data-trend', rowData.trendStats?.trendValsStr || '')
    .attr('data-dates', rowData.trendStats?.trendDatesStr || '')
    .attr('data-title', rowData.title);

  $tds.eq(2)
    .addClass('td-trend')
    .attr('data-t7', rowData.trendStats?.t7 || 0)
    .attr('data-t30', rowData.trendStats?.t30 || 0)
    .attr('data-t60', rowData.trendStats?.t60 || 0)
    .attr('data-tall', rowData.trendStats?.tall || 0)
    .attr('data-order', rowData.trendStats?.t7 || 0);

  $tds.eq(3)
    .addClass('td-votes')
    .attr('data-rv', rowData.votes?.redVotes || 0)
    .attr('data-rp', rowData.votes?.redPercent || 50)
    .attr('data-bv', rowData.votes?.blackVotes || 0)
    .attr('data-bp', rowData.votes?.blackPercent || 50)
    .attr('data-order', rowData.votes?.redVotes || 0);

  $tds.eq(4)
    .addClass('td-engage td-comment')
    .attr('data-rec', rowData.recommendations || 0)
    .attr('data-fav', rowData.favorites || 0)
    .attr('data-com', rowData.commentsCount || 0)
    .attr('data-order', rowData.commentsCount || 0)
    .attr('data-mid', rowData.mid);

  $tds.eq(5)
    .addClass('td-tags')
    .attr('data-search', (rowData.tags || []).join(' '))
    .attr('data-cat-search', (rowData.categories || []).join(','))
    .attr('data-count', (rowData.categories || []).length)
    .attr('data-order', (rowData.categories || []).length);

  $tds.eq(6)
    .addClass('td-mods')
    .attr('data-search', rowData.modSearchText || '')
    .attr('data-count', rowData.includedModsCount || 0)
    .attr('data-order', rowData.includedModsCount || 0);
}
