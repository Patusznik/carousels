// UI layer for the "os" layout: macOS / iOS-style elements drawn in the theme palette (original drawings, no Apple logos).
// Each element: { type, at: "x,y" (% of the slide) | top|upper|center|lower|bottom[-left|-right], w (px), rot (deg),
//                 layer: "front" | "behind" (between the photo and your cut-out), …type fields }.
const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const inline = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>').replace(/\|/g, '<br>');

const SPOTS = { top: 12, upper: 28, center: 50, middle: 50, lower: 70, bottom: 87 };
export function place(at, dflt = 'center') {
  const a = String(at || dflt).trim();
  const m = a.match(/^(L|R|C|-?[\d.]+)\s*,\s*(-?[\d.]+)$/i);   // "40,70" centre at 40 %/70 %;  "L,70" / "R,70" = against the left / right edge
  if (m) { const c = m[1].toUpperCase(); return c === 'L' ? { x: 6, y: +m[2], ax: 0 } : c === 'R' ? { x: 94, y: +m[2], ax: 1 } : c === 'C' ? { x: 50, y: +m[2], ax: 0.5 } : { x: +m[1], y: +m[2], ax: 0.5 }; }
  const [v, h] = a.split('-');
  const y = SPOTS[v] ?? 50;
  if (h === 'left') return { x: 6, y, ax: 0 };
  if (h === 'right') return { x: 94, y, ax: 1 };
  return { x: 50, y, ax: 0.5 };
}

const ICONS = {
  arrowUp: '<svg viewBox="0 0 24 24"><path d="M12 19V5M5.5 11.5 12 5l6.5 6.5" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  heart: '<svg viewBox="0 0 24 24"><path d="M12 20.5s-7.5-4.6-7.5-10.1A4.3 4.3 0 0 1 12 7.7a4.3 4.3 0 0 1 7.5 2.7c0 5.5-7.5 10.1-7.5 10.1z" fill="currentColor"/></svg>',
  call: '<svg viewBox="0 0 24 24"><path d="M6.6 3.5h3l1.5 4-2 1.3a11 11 0 0 0 6.1 6.1l1.3-2 4 1.5v3a2 2 0 0 1-2.2 2A17.5 17.5 0 0 1 4.6 5.7a2 2 0 0 1 2-2.2z" fill="currentColor"/></svg>',
  moon: '<svg viewBox="0 0 24 24"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z" fill="currentColor"/></svg>',
  check: '<svg viewBox="0 0 24 24"><path d="M5 12.5 10 17.5 19 7" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  folder: '<svg viewBox="0 0 24 24"><path d="M3 6.5A1.5 1.5 0 0 1 4.5 5h4.6l2 2h8.4A1.5 1.5 0 0 1 21 8.5v9a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17.5z" fill="currentColor"/></svg>',
  photo: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="m5 17 5-5 3.5 3.5L16 13l3 4" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  desktop: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M9 20h6M12 16v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  down: '<svg viewBox="0 0 24 24"><path d="M12 4v12M6.5 10.5 12 16l5.5-5.5M5 20h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  wifi: '<svg viewBox="0 0 24 24"><path d="M2.5 9a14 14 0 0 1 19 0M5.5 12.3a9.5 9.5 0 0 1 13 0M8.6 15.6a5 5 0 0 1 6.8 0" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="19" r="1.6" fill="currentColor"/></svg>',
  battery: '<svg viewBox="0 0 30 24"><rect x="1.5" y="6" width="24" height="12" rx="3.5" fill="none" stroke="currentColor" stroke-width="1.8"/><rect x="4" y="8.5" width="16" height="7" rx="1.6" fill="currentColor"/><path d="M27.5 10v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
  search: '<svg viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="m15 15 5 5" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>',
  dots: '<svg viewBox="0 0 24 24"><circle cx="5" cy="12" r="2" fill="currentColor"/><circle cx="12" cy="12" r="2" fill="currentColor"/><circle cx="19" cy="12" r="2" fill="currentColor"/></svg>',
  bookmark: '<svg viewBox="0 0 24 24"><path d="M6 3h12v18l-6-4.5L6 21z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  send: '<svg viewBox="0 0 24 24"><path d="M21 3 10 14M21 3l-7 18-4-7-7-4z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  comment: '<svg viewBox="0 0 24 24"><path d="M20 11.5a8 8 0 0 1-11.6 7.1L4 20l1.3-4.2A8 8 0 1 1 20 11.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  likeO: '<svg viewBox="0 0 24 24"><path d="M12 20.5s-7.5-4.6-7.5-10.1A4.3 4.3 0 0 1 12 7.7a4.3 4.3 0 0 1 7.5 2.7c0 5.5-7.5 10.1-7.5 10.1z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  film: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M7 5v14M17 5v14M3 9.5h4M3 14.5h4M17 9.5h4M17 14.5h4" stroke="currentColor" stroke-width="2"/></svg>',
  warn: '<svg viewBox="0 0 24 24"><path d="M12 3.5 22 20H2z" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/><path d="M12 10v4.5" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><circle cx="12" cy="17.3" r="1.4" fill="currentColor"/></svg>',
  sparkle: '<svg viewBox="0 0 24 24"><path d="M12 2c.7 4.8 2.7 7.3 10 10-7.3 2.7-9.3 5.2-10 10-.7-4.8-2.7-7.3-10-10 7.3-2.7 9.3-5.2 10-10z" fill="currentColor"/></svg>',
};
const CURSOR = '<svg viewBox="0 0 32 40"><path d="M3 2v30l8-7.5 5 11 5.2-2.3-5-10.7H27z" fill="#111" stroke="#fff" stroke-width="2.6" stroke-linejoin="round"/></svg>';
const lights = '<span class="tl"><i></i><i></i><i></i></span>';

function select(text, sel) {          // highlight a substring with text-selection handles
  const t = esc(text); if (!sel) return inline(text);
  const i = text.indexOf(sel); if (i < 0) return inline(text);
  return inline(text.slice(0, i)) + `<span class="sel">${esc(sel)}</span>` + inline(text.slice(i + sel.length));
}

const T = {
  bubble: (e) => `<div class="u-bubble ${e.side === 'out' ? 'out' : 'in'}">${inline(e.text)}${e.time ? `<span class="tm">${esc(e.time)}${e.side === 'out' ? ' ✓✓' : ''}</span>` : ''}</div>`,
  input: (e) => `<div class="u-input"><span class="tx">${select(e.text, e.select)}</span>${e.send === false ? '' : `<span class="go">${ICONS.arrowUp}</span>`}</div>`,
  dialog: (e, A) => {
    const b = String(e.buttons || 'Cancel|OK').split('|'), p = e.primary != null ? +e.primary : b.length - 1;
    return `<div class="u-dialog">${A.icon ? `<img class="ic" src="${A.icon}">` : e.glyph ? `<div class="ic g">${ICONS[e.glyph] || esc(e.glyph)}</div>` : ''}
      ${e.title ? `<div class="ti">${inline(e.title)}</div>` : ''}${e.text ? `<div class="tx">${inline(e.text)}</div>` : ''}
      ${e.buttons === '' || e.buttons === 'none' ? '' : `<div class="bt">${b.map((x, k) => `<span class="${k === p ? 'pri' : ''}" ${k === p ? 'data-cursor' : ''}>${esc(x)}</span>`).join('')}</div>`}</div>`;
  },
  notif: (e, A) => `<div class="u-notif">${A.icon ? `<img class="ic" src="${A.icon}">` : `<div class="ic g">${ICONS[e.glyph || 'check'] || ''}</div>`}
      <div class="bd"><div class="hd"><span>${esc(e.app || 'Carousels')}</span><span>${esc(e.time || 'now')}</span></div>
      ${e.title ? `<div class="ti">${inline(e.title)}</div>` : ''}${e.text ? `<div class="tx">${inline(e.text)}</div>` : ''}</div></div>`,
  pill: (e) => `<div class="u-pill"><span class="ic">${ICONS[e.glyph || 'heart'] || ''}</span><span class="bd"><b>${inline(e.label || '')}</b>${e.sub ? `<small>${inline(e.sub)}</small>` : ''}</span>
      ${e.glyph === 'call' ? '<span class="cb no">' + ICONS.call + '</span><span class="cb yes">' + ICONS.call + '</span>' : ''}</div>`,
  counter: (e, A, s) => `<div class="u-counter">${esc(e.text || `${s.n}/${s.total}`)}</div>`,
  cursor: () => `<div class="u-cursor">${CURSOR}</div>`,
  sticker: (e, A) => A.stk ? `<img class="u-sticker" src="${A.stk}">` : '',
  image: (e, A) => A.img ? `<img class="u-image${e.shadow === 'off' ? '' : ' sh'}" src="${A.img}">` : '',
  sticky: (e) => `<div class="u-sticky">${inline(e.text)}</div>`,
  spark: (e) => `<div class="u-spark">${ICONS.sparkle}</div>`,
  folder: (e, A) => `<div class="u-folder${A.stk ? ' with' : ''}">
      <svg class="back" viewBox="0 0 100 80"><path d="M4 10a6 6 0 0 1 6-6h24l8 8h48a6 6 0 0 1 6 6v54a6 6 0 0 1-6 6H10a6 6 0 0 1-6-6z" fill="var(--fold-back)"/></svg>
      ${A.stk ? `<img class="who" src="${A.stk}">` : ''}
      <svg class="front" viewBox="0 0 100 80"><path d="M4 26a6 6 0 0 1 6-6h80a6 6 0 0 1 6 6v46a6 6 0 0 1-6 6H10a6 6 0 0 1-6-6z" fill="var(--fold-front)"/><path d="M4 27a6 6 0 0 1 6-6h80a6 6 0 0 1 6 6" fill="none" stroke="rgba(255,255,255,.45)" stroke-width="1"/></svg>
      ${e.label ? `<div class="lb"><i style="background:var(--${e.tag || 'terracotta'})"></i>${esc(e.label)}</div>` : ''}</div>`,
  profile: (e, A) => `<div class="u-profile"><div class="top"><span class="av">${A.avatar ? `<img src="${A.avatar}">` : `<b>${esc((e.name || 'C')[0])}</b>`}</span>
      <div class="nm"><b>${esc(e.name || '')}</b>${e.stats ? `<div class="st">${String(e.stats).split('|').map(x => { const [v, l] = x.trim().split(/\s+(.+)/); return `<span><b>${esc(v)}</b>${esc(l || '')}</span>`; }).join('')}</div>` : ''}</div></div>
      ${e.bio ? `<div class="bio">${inline(e.bio)}</div>` : ''}<div class="fl" data-cursor>${esc(e.follow || 'Follow')}</div></div>`,
  window: (e, A, s) => {
    const kind = e.kind || (e.lines ? 'terminal' : e.rows ? 'list' : e.photos ? 'finder' : e.before ? 'compare' : e.photo ? 'preview' : 'text');
    let body = '';
    if (kind === 'text') body = `<div class="w-text">${e.kicker ? `<div class="kk">${esc(e.kicker)}</div>` : ''}${e.title ? `<div class="tt">${inline(e.title)}</div>` : ''}${e.body ? `<div class="bb">${inline(e.body)}</div>` : ''}</div>`;
    if (kind === 'terminal') body = `<div class="w-term">${String(e.lines || '').split('|').map(l => {
        const L = l.replace(/^\s+/, ''); const cls = L.startsWith('$') ? 'cmd' : L.startsWith('>') ? 'say' : /✓|done|ready/i.test(L) ? 'ok' : L.startsWith('!') ? 'warn' : '';
        return `<div class="${cls}">${esc(L).replace(/^\$/, '<span class="ps">~ %</span>')}</div>`; }).join('')}<div class="cmd"><span class="ps">~ %</span><span class="caret"></span></div></div>`;
    if (kind === 'list') {                 // app list (Force Quit style): rows "Name (status)|…", pick = highlighted row, button
      const rows = String(e.rows).split('|');
      body = `<div class="w-list">${e.kicker ? `<div class="lh">${inline(e.kicker)}</div>` : ''}<div class="rows">${rows.map((r, k) => {
        const m = r.match(/^(.*?)\s*(\(.*\))?$/); const nm = m[1].trim();
        return `<div class="${k === +(e.pick ?? -1) ? 'on' : ''}"><i style="background:${['var(--terracotta)', 'var(--plum)', 'var(--espresso2)', 'var(--terracotta2)'][k % 4]}">${esc(nm[0] || '')}</i><span>${esc(nm)}</span>${m[2] ? `<small>${esc(m[2])}</small>` : ''}</div>`; }).join('')}</div>
        ${e.button ? `<div class="bt"><span data-cursor>${esc(e.button)}</span></div>` : ''}</div>`;
    }
    if (kind === 'preview') body = `<div class="w-prev" style="height:${A.h}px"><img src="${A.ph}"></div>`;
    if (kind === 'compare') body = `<div class="w-cmp" style="height:${A.h}px"><div><img src="${A.before}"><span>${esc(e.left || 'before')}</span></div><div><img src="${A.ph}"><span>${esc(e.right || 'after')}</span></div><b class="hd">‹ ›</b></div>`;
    if (kind === 'finder') {
      const names = String(e.names || e.photos).split(',').map(x => x.trim());
      body = `<div class="w-find"><div class="sb"><small>Favourites</small>${[['desktop', 'Desktop'], ['down', 'Downloads'], ['photo', 'Photos'], ['folder', e.folder || 'carousels']].map(([i, n], k) =>
        `<div class="${k === 3 ? 'on' : ''}">${ICONS[i]}${esc(n)}</div>`).join('')}</div><div class="gr">${(A.thumbs || []).map((u, k) =>
        `<figure class="${k === +(e.pick ?? -1) ? 'on' : ''}">${u ? `<img src="${u}">` : '<div class="ph0"></div>'}<figcaption>${esc(names[k] || '')}</figcaption></figure>`).join('')}</div></div>`;
    }
    return `<div class="u-window ${kind}"><div class="bar">${lights}<span class="wt">${esc(e.title_bar || e.name || '')}</span>${kind === 'finder' ? `<span class="srch">${ICONS.search}</span>` : ''}</div>${body}</div>`;
  },
  post: (e, A) => `<div class="u-post"><div class="hd"><span class="av">${A.avatar ? `<img src="${A.avatar}">` : ''}</span><b>${esc(e.name || '')}</b><span class="dt">${ICONS.dots}</span></div>
      <div class="ph" style="height:${A.h}px"><img src="${A.ph}"></div><div class="ac"><span>${ICONS.likeO}</span><span>${ICONS.comment}</span><span>${ICONS.send}</span><span class="sv">${ICONS.bookmark}</span></div>
      ${e.text ? `<div class="cp">${inline(e.text)}</div>` : ''}</div>`,
};

function arrow(e, s, W, H) {
  const pt = v => String(v).split(',').map(Number);
  const [x1, y1] = pt(e.from || '30,40').map((v, i) => v / 100 * (i ? H : W)), [x2, y2] = pt(e.to || '60,60').map((v, i) => v / 100 * (i ? H : W));
  const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy), b = +(e.bend ?? 0.3);
  const cx = (x1 + x2) / 2 - dy * b, cy = (y1 + y2) / 2 + dx * b;          // control point off to one side
  const ang = Math.atan2(y2 - cy, x2 - cx), hl = Math.min(54, len * 0.22);
  const head = [ang + 2.6, ang - 2.6].map(a => `M ${x2 + Math.cos(a) * hl} ${y2 + Math.sin(a) * hl} L ${x2} ${y2}`).join(' ');
  const d = `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2} ${head}`;
  return `<svg class="u-arrow" viewBox="0 0 ${W} ${H}"><path d="${d}" class="halo"/><path d="${d}" class="ln"/></svg>`;
}

export function uiElement(e, k, s) {
  if (e.type === 'arrow') return arrow(e, s, s._W || 1080, s._H || 1350);
  const p = place(e.at, e.type === 'counter' ? '6,5' : 'center');
  if (e.type === 'counter' && !e.at) { p.x = 94; p.y = 5.5; p.ax = 1; }
  const A = (s.ui_assets || {})[k] || {};
  const html = (T[e.type] || (() => `<div class="u-bubble in">unknown ui type ${esc(e.type)}</div>`))(e, A, s);
  const w = e.w ? `width:${e.w}px;` : '';
  const auto = e.type === 'cursor' && !e.at ? ' data-auto' : '';
  return `<div class="ui ${e.layer === 'behind' ? 'behind' : 'front'}"${auto} data-k="${k}" data-type="${esc(e.type)}" style="left:${p.x}%;top:${p.y}%;${w}transform:translate(${-p.ax * 100}%,-50%) rotate(${+e.rot || 0}deg)">${html}</div>`;
}

export const menubar = (s, D) => `<div class="u-menubar"><span class="lg">●</span><b>${esc(s.app || 'Carousels')}</b>${['File', 'Edit', 'View', 'Slide', 'Window', 'Help'].map(m => `<span>${m}</span>`).join('')}
  <span class="rt">${ICONS.wifi}${ICONS.battery}<span>${esc(s.clock || D.clock || 'Thu 9:41')}</span></span></div>`;

// cursors marked "auto" point at the primary button of a dialog / the Follow button on the same slide
export function aimCursors(el) {
  const slide = el.getBoundingClientRect();
  for (const c of el.querySelectorAll('.ui[data-type="cursor"][data-auto]')) {
    const t = el.querySelector('[data-cursor]'); if (!t) continue;
    const r = t.getBoundingClientRect();
    c.style.left = ((r.left + r.width * 0.62 - slide.left) / slide.width * 100) + '%';
    c.style.top = ((r.top + r.height * 0.72 - slide.top) / slide.height * 100) + '%';
    c.style.transform = 'translate(-8%,-6%)';
  }
}
