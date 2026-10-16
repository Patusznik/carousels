// Renders one slide at a time from data/slides.json (written by render.py). window.renderSlide(i) → true when laid out.
import { uiElement, menubar, aimCursors } from './ui.js';
const DATA = await (await fetch('data/slides.json')).json();
const { W, H, theme, slides, strings } = DATA;
const root = document.documentElement;
root.style.setProperty('--W', W + 'px'); root.style.setProperty('--H', H + 'px');
for (const [k, v] of Object.entries(theme.colors)) root.style.setProperty('--' + k, v);
const rgb = h => { const m = String(h).match(/^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i); return m ? m.slice(1).map(x => parseInt(x, 16)).join(',') : null; };
if (rgb(theme.colors.espresso)) root.style.setProperty('--ink-rgb', rgb(theme.colors.espresso));
root.style.setProperty('--grain', theme.grain ?? 0.15);
// fonts: theme.fonts picks the family per role; theme.font_faces adds extra files from templates/fonts (e.g. from a reference look)
const F = { display: 'Anton', accent: 'ISerif', body: 'Inter', label: 'JBMono', mono: 'JBMono', ...(theme.fonts || {}) };
for (const [k, v] of Object.entries(F)) root.style.setProperty('--f-' + k, String(v).split(',').map(x => `"${x.trim()}"`).join(', '));
if (theme.font_faces?.length) {
  const st = document.createElement('style');
  const R = { latin: 'U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD',
              'latin-ext': 'U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF' };
  st.textContent = theme.font_faces.map(f => `@font-face { font-family: "${f.family}"; src: ${(f.local || []).map(n => `local("${n}")`).concat(f.file ? [`url(fonts/${f.file})`] : []).join(', ')}; font-weight: ${f.weight || 400}; font-style: ${f.style || 'normal'};${f.range ? ` unicode-range: ${R[f.range] || f.range};` : ''} }`).join('\n');
  document.head.appendChild(st);
}
const el = document.getElementById('slide');

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
// markup: "|" or newline = line break, *word* = serif italic accent, **word** = bold (body)
const inline = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>');
const fmtTitle = s => inline(s).replace(/\s*\|\s*/g, '<br>').replace(/\n/g, '<br>');
const lines = s => /[|\n]/.test(String(s ?? '')) ? ' lines' : '';
const fmtBody = s => String(s ?? '').split(/\n\s*\n/).map(p => `<p>${inline(p).replace(/\n/g, '<br>')}</p>`).join('');
const pad = n => String(n).padStart(2, '0');

const ICON = {
  save: '<svg viewBox="0 0 24 24"><path d="M6 3h12v18l-6-4.5L6 21z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  share: '<svg viewBox="0 0 24 24"><path d="M21 3 10 14M21 3l-7 18-4-7-7-4z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
  comment: '<svg viewBox="0 0 24 24"><path d="M4 5h16v11H9l-5 4z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>',
};

// shrink a block's font until it fits its box (keeps the designed size when it already fits)
function fit(node, maxPx, minPx, maxW, maxH) {
  if (!node) return;
  let px = maxPx; node.style.fontSize = px + 'px';
  for (let i = 0; i < 60; i++) {
    const tooWide = node.scrollWidth > (maxW ?? node.clientWidth) + 1;
    const tooTall = maxH && node.scrollHeight > maxH + 1;
    if ((!tooWide && !tooTall) || px <= minPx) break;
    px = Math.max(minPx, px * 0.96); node.style.fontSize = px + 'px';
  }
}

function chrome(s, { swipe = false } = {}) {
  const kicker = s.kicker ? `<span class="label">${esc(s.kicker)}</span>` : '<span></span>';
  const counter = s.counter !== false ? `<span class="label">${pad(s.n)} / ${pad(s.total)}</span>` : '';
  const handle = DATA.handle ? `<span class="label">${esc(DATA.handle)}</span>` : '<span></span>';
  const sw = swipe ? `<span class="label swipe">${esc(strings.swipe)}</span>` : '';
  return `<div class="meta">${kicker}${counter}</div><div class="foot">${handle}${sw}</div><div class="grain"></div>`;
}

const LAYOUTS = {
  cover: s => {
    const im = (src, cls) => s.head_px != null ? `<img class="strip ${cls}" id="${cls}" src="${src}" style="height:${s.box.h}px;top:0">` : `<img class="fill ${cls}" src="${src}">`;
    return `${im(s.assets.ph, 'ph')}<div class="fill shade-top"></div><div class="fill shade-bot"></div>
    <div class="title disp${lines(s.title)}" id="t">${fmtTitle(s.title)}</div>${s.assets.cut ? im(s.assets.cut, 'cut') : ''}
    ${s.body ? `<div class="sub body" id="b">${inline(s.body)}</div>` : ''}${chrome(s, { swipe: true })}`; },
  'cover-sticker': s => `<div class="sun"></div><div class="title disp${lines(s.title)}" id="t">${fmtTitle(s.title)}</div>
    ${s.body ? `<div class="sub body" id="b">${fmtBody(s.body)}</div>` : ''}
    ${s.assets.stk ? `<img class="stk" src="${s.assets.stk}" style="width:${s.box.w}px;height:${s.box.h}px">` : ''}${chrome(s, { swipe: true })}`,
  photo: s => `<img class="fill" src="${s.assets.ph}"><div class="fill shade-top"></div><div class="fill shade-bot"></div>
    <div class="cap">${s.title ? `<div class="title disp${lines(s.title)}" id="t">${fmtTitle(s.title)}</div>` : ''}${s.body ? `<div class="body" id="b">${fmtBody(s.body)}</div>` : ''}</div>${chrome(s)}`,
  split: s => `<div class="ph-box" style="height:${s.box.h}px"><img class="fill" src="${s.assets.ph}"></div>
    <div class="txt"><div class="rule"></div>${s.title ? `<div class="title disp${lines(s.title)}" id="t">${fmtTitle(s.title)}</div>` : ''}${s.body ? `<div class="body" id="b">${fmtBody(s.body)}</div>` : ''}</div>${chrome(s)}`,
  text: s => `<div class="num">${pad(s.n)}</div><div class="txt">${s.title ? `<div class="title disp${lines(s.title)}" id="t">${fmtTitle(s.title)}</div>` : ''}${s.body ? `<div class="body" id="b">${fmtBody(s.body)}</div>` : ''}</div>
    ${s.assets.stk ? `<img class="stk" src="${s.assets.stk}" style="width:${s.box.w}px;height:${s.box.h}px">` : ''}${chrome(s)}`,
  list: s => `<div class="txt">${s.title ? `<div class="title disp${lines(s.title)}" id="t">${fmtTitle(s.title)}</div>` : ''}
    ${(s.items || []).map((it, k) => `<div class="item"><span class="n">${pad(k + 1)}</span><span class="t">${inline(it)}</span></div>`).join('')}</div>${chrome(s)}`,
  quote: s => `<div class="mark">“</div><div class="q"><div class="qi" id="q">${inline(s.quote || s.title)}</div></div>${s.by ? `<div class="by label">— ${esc(s.by)}</div>` : ''}${chrome(s)}`,
  cta: s => `<div class="title disp${lines(s.title || strings.cta_title)}" id="t">${fmtTitle(s.title || strings.cta_title)}</div>
    <div class="acts">${(s.actions || ['save', 'share', 'comment']).map(a => `<div class="act"><i>${ICON[a] || ''}</i>${esc((s.labels || {})[a] || strings[a] || a)}</div>`).join('')}</div>
    ${s.body ? `<div class="body" id="b">${inline(s.body)}</div>` : ''}
    ${s.assets.stk ? `<img class="stk" src="${s.assets.stk}" style="width:${s.box.w}px;height:${s.box.h}px">` : ''}${chrome(s)}`,
};
LAYOUTS.os = s => {                       // photo (or desktop wallpaper) + UI elements; your cut-out can sit in front of them
  const ph = !!s.assets.ph, strip = s.head_px != null;
  const img = (src, cls) => strip ? `<img class="${cls} strip" id="${cls}" src="${src}" style="height:${s.box.h}px;top:0">` : `<img class="${cls}" id="${cls}" src="${src}">`;
  let h = ph ? img(s.assets.ph, 'ph') + (s.assets.cut ? img(s.assets.cut, 'cut') : '') + (s.title || s.menubar ? '<div class="shade" id="shade"></div>' : '')
             : `<div class="desk${s.bg === 'plain' ? ' plain' : ''}"></div>`;
  if (s.menubar) h += menubar(s, DATA);
  if (s.title) h += `<div class="big${lines(s.title)}" id="t">${fmtTitle(s.title)}</div>`;
  if (s.body) h += `<div class="sub" id="b">${inline(s.body)}</div>`;
  if (s.person_box && s.select_person) h += `<div class="u-selbox" id="selbox"><i></i><i></i><i></i><i></i><i></i><i></i>${s.select_person === true || s.select_person === 'on' ? '' : `<span>${esc(s.select_person)}</span>`}</div>`;
  s._W = W; s._H = H; (s.ui || []).forEach((e, k) => { h += uiElement(e, k, s); });
  if (s.counter === true && !(s.ui || []).some(e => e.type === 'counter')) h += uiElement({ type: 'counter' }, -1, s);   // slide counter only on request
  return h + '<div class="grain"></div>';
};
const PHOTO_BG = new Set(['cover', 'photo']);
// designed title sizes per layout: [max px, min px, max height]
const TITLE = { cover: [220, 90, 470], 'cover-sticker': [190, 80, 470], photo: [118, 64, 400], split: [104, 60, 300],
                text: [130, 70, 520], list: [104, 60, 260], cta: [190, 90, 470] };

window.renderSlide = async (i) => {
  const s = slides[i];
  el.className = `slide L-${s.layout}` + (PHOTO_BG.has(s.layout) ? ' on-photo' : '') + (s.layout === 'os' ? (s.assets.ph ? ' photo-bg' : ' desk-bg') : '');
  el.innerHTML = (LAYOUTS[s.layout] || LAYOUTS.text)(s);
  await Promise.all([...el.querySelectorAll('img')].map(im => im.complete ? 1 : new Promise(r => { im.onload = r; im.onerror = r; })));
  await document.fonts.ready;
  const [mx, mn, mh] = TITLE[s.layout] || [120, 60, 400];
  const t = document.getElementById('t'), b = document.getElementById('b'), q = document.getElementById('q');
  const bodyPx = b ? parseFloat(getComputedStyle(b).fontSize) : 0;
  if (s.layout === 'os') {
    const tp = s.title_pos || 'top', top0 = s.menubar ? 120 : 100;
    if (t) {
      t.style.top = (tp === 'bottom' ? H - 170 - (s.title_h || 380) : top0) + 'px';
      fit(t, s.title_size || (tp === 'behind' ? 230 : 150), 64, t.clientWidth, s.title_h || (tp === 'behind' ? 470 : 380));
      if (tp === 'bottom') t.style.top = (H - 150 - t.offsetHeight - (b ? b.offsetHeight + 24 : 0)) + 'px';
    }
    if (b) {
      if (s.body_pos === 'bottom' || (s.assets.ph && s.body_pos !== 'under')) { b.style.bottom = '120px'; b.style.top = 'auto'; }
      else b.style.top = ((t ? t.getBoundingClientRect().bottom - el.getBoundingClientRect().top : top0) + 28) + 'px';
      if (tp === 'bottom' && t) { b.style.top = (t.offsetTop + t.offsetHeight + 24) + 'px'; b.style.bottom = 'auto'; }
    }
  } else if (s.layout === 'photo' || s.layout === 'split') {             // bottom-anchored text: title + body share the room under the photo
    const limitTop = s.layout === 'photo' ? H * 0.42 : s.box.h + 56;
    const room = H - 150 - limitTop - (s.layout === 'split' ? 36 : 0);
    if (t) fit(t, s.title_size || mx, mn, t.clientWidth, Math.min(mh, room * (b ? 0.55 : 1)));
    if (b) fit(b, bodyPx, 24, b.clientWidth, room - (t ? t.offsetHeight + 24 : 0));
  } else {
    if (t) fit(t, s.title_size || mx, mn, t.clientWidth, mh);
    if (q) fit(q, s.title_size || ((s.quote || s.title || '').length < 70 ? 124 : 96), 52, q.parentElement.clientWidth, H - 400 - 260);
    if (b && s.layout !== 'cover') fit(b, bodyPx, 24, b.clientWidth, H - 150 - b.getBoundingClientRect().top);
  }
  const sh = s.shade ?? 0.3, st = el.querySelector('.shade-top'), sb = el.querySelector('.shade-bot');   // darker on busy/bright photos
  if (s.layout === 'cover' && st) st.style.background = `linear-gradient(to bottom, rgba(30,22,18,${0.5 + 0.32 * sh}), rgba(30,22,18,${0.12 + 0.3 * sh}) ${38 + 10 * sh}%, rgba(30,22,18,0) ${58 + 12 * sh}%)`;
  if (s.layout === 'photo' && sb) sb.style.background = `linear-gradient(to top, rgba(30,22,18,${0.74 + 0.16 * sh}), rgba(30,22,18,${0.42 + 0.2 * sh}) 30%, rgba(30,22,18,0) ${58 + 8 * sh}%)`;
  const stk = el.querySelector('.L-cover-sticker .stk');
  if (stk && t) {                                                  // keep her head clear of the title: push the sticker down
    const head = stk.getBoundingClientRect().top + 0.06 * s.box.h, tb = t.getBoundingClientRect().bottom + 12;
    if (head < tb) stk.style.bottom = (-40 - Math.min(260, tb - head)) + 'px';
  }
  let off = 0;
  if ((s.layout === 'cover' || s.layout === 'os') && s.head_px != null && t) {   // slide the photo so her head tucks under the last title line
    const r = t.getBoundingClientRect(), fs = parseFloat(getComputedStyle(t).fontSize);
    const target = r.bottom - el.getBoundingClientRect().top - 0.14 * fs * (s.overlap ?? 1);   // overlap 0 = head just under the title, 3 = deeper
    off = Math.min(0, Math.max(H - s.box.h, target - s.head_px));
    for (const id of ['ph', 'cut']) { const im = document.getElementById(id); if (im) im.style.top = off + 'px'; }
  }
  const sb_ = document.getElementById('selbox');
  if (sb_ && s.person_box) { const [x, y, w, h] = s.person_box; Object.assign(sb_.style, { left: x + 'px', top: (y + off) + 'px', width: w + 'px', height: h + 'px' }); }
  const sh_ = document.getElementById('shade');
  if (sh_) { const k = s.shade ?? 0.3; sh_.style.background = `linear-gradient(to bottom, rgba(30,22,18,${0.34 + 0.34 * k}), rgba(30,22,18,${0.08 + 0.22 * k}) 36%, rgba(30,22,18,0) 56%)` +
             (b && s.assets.ph ? `, linear-gradient(to top, rgba(30,22,18,${0.45 + 0.25 * k}), rgba(30,22,18,0) 32%)` : ''); }
  aimCursors(el);
  await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
  return true;
};
window.ready = true;
