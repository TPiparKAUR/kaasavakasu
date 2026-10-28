  /* ---------- kaasneva kasu jagatud abifunktsioonid ---------- */
  const STATE_IX = { vilets: 0, keskmine: 1, hea: 2 };
  const stCol = (name) => (name in STATE_IX ? stateColor(STATE_IX[name]) : cssVar('--neutral'));
  const stInk = (name) => (name in STATE_IX ? stateInk(STATE_IX[name]) : cssVar('--muted'));
  const ECO_SHORT = { 1: 'Niit', 2: 'Soo', 3: 'Mets', 31: 'Kuivad metsad', 32: 'Märjad metsad', 4: 'Põld', 5: 'Rannik', 6: 'Asustus ja muu' };
  const ST = { OK: 0, PART: 1, NONE: 2, MISS: 3, MIX: 4 };
  function K() { return D.K; }
  function kIndex() {
    if (!D.kx) {
      const ind = new Map(D.K.indikaatorid.map((i) => [i.key, i]));
      const lay = new Map(D.K.kihid.map((l, i) => [l.id, i]));
      D.kx = { ind, lay };
    }
    return D.kx;
  }
  /** Rakk (mediaan, keskmine, kate, esineb_osa, staatus, mediaan > 0) → { v (mediaan), mean, st, cls } kuvamiseks. */
  function cellView(c) {
    if (!c) return { v: null, mean: null, st: null, txt: '', cls: 'na' };
    const [med, mean, , , st] = c;
    if (st === ST.NONE) return { v: null, mean, st, txt: 'ei paku', cls: 'none' };
    if (st === ST.MISS || med === null) return { v: null, mean, st, txt: '–', cls: 'miss' };
    return { v: med, mean, st, txt: fmt(med), cls: st === ST.PART ? 'part' : 'ok' };
  }
  function flagsOf(l) { return `${l.definitsiooniline ? ' †' : ''}${l.madal_lahutus ? ' ‡' : ''}${l.nodata_valja ? ' §' : ''}`; }
  function unitShort(u) { return (u || '').split(' (')[0]; }
  function csvQ(v) { return v === null || v === undefined ? '' : typeof v === 'string' ? `"${v.replaceAll('"', '""')}"` : String(v); }
  function saveText(name, text, mime = 'text/csv;charset=utf-8') {
    const blob = new Blob(['﻿', text], { type: mime });
    const a = h('a', { href: URL.createObjectURL(blob), download: name }); document.body.append(a); a.click(); a.remove();
  }
  function navTo(sec, tab) {
    S.sec = sec; if (tab) S.tab = tab;
    if (location.hash !== `#${sec}`) { try { history.replaceState(null, '', `#${sec}`); } catch { /* file:// */ } }
    renderAll(true); scrollTo(0, 0);
  }
  function btn(parent, text, cls, on) { const b = h('button', { type: 'button', class: cls }, parent, text); b.onclick = on; return b; }
  function pill(parent, text, cls, title) { return h('span', { class: `pill ${cls || ''}`, title: title || null }, parent, text); }
  function xlsxLink(parent, text) {
    const x = window.__OKS__ ? window.__OKS__.xlsx : undefined;
    if (x === false) return h('span', { class: 'btn muted', title: 'Excel on allalaaditav GitHub Pages saidilt ja ühefailsest versioonist' }, parent, 'Excel: vt GitHub Pages');
    return h('a', { class: 'btn primary', href: x || 'andmetabel_kaasneva_kasu.xlsx', download: 'andmetabel_kaasneva_kasu.xlsx' }, parent, text || 'Laadi alla Excel');
  }
  /** Staatuse märgend (legend). */
  function statusLegend(parent) {
    const lg = h('ul', { class: 'legend' }, parent);
    for (const [cls, t] of [['ok', 'väärtus (mediaan kogu klassi pindala kohta, nullid kaasa arvatud)'], ['part', 'kaldkiri ja kollane: osaline kate (kehtivaid piksleid alla 90 %)'], ['none', 'ei paku: nullist erinevaid piksleid alla 1 % (lähtekasu „väga-väga vähe“)'], ['miss', '–: teenust ei hinnatud (kehtivaid piksleid alla 5 %)']]) {
      const li = h('li', {}, lg); h('span', { class: `cellkey ${cls}` }, li, cls === 'none' ? 'ei paku' : cls === 'miss' ? '–' : '12,3'); h('span', {}, li, t);
    }
  }
