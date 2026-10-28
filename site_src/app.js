/* Ökosüsteemiteenused ja seisund – interaktiivne vaade (ilma välisteekideta). */
(() => {
  'use strict';

  /* ---------- abifunktsioonid ---------- */
  const SVG = new Set(['svg', 'g', 'rect', 'line', 'path', 'circle', 'text', 'title', 'polygon', 'polyline']);
  const NS = 'http://www.w3.org/2000/svg';
  function h(tag, attrs, parent, text) {
    const e = SVG.has(tag) ? document.createElementNS(NS, tag) : document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) if (v !== null && v !== undefined && v !== false) e.setAttribute(k, v === true ? '' : v);
    if (text !== undefined && text !== null) e.textContent = text;
    if (parent) parent.append(e);
    return e;
  }
  const $ = (s, r = document) => r.querySelector(s);
  const nfs = {};
  const nf = (d) => (nfs[d] ||= new Intl.NumberFormat('et-EE', { minimumFractionDigits: d, maximumFractionDigits: d }));
  function fmt(x, sig) {
    if (x === null || x === undefined || !Number.isFinite(x)) return '–';
    const a = Math.abs(x);
    if (a === 0) return '0';
    if (a >= 1000) return nf(0).format(x);
    if (a >= 100) return nf(1).format(x);
    if (a >= 10) return nf(sig ? 1 : 1).format(x);
    if (a >= 1) return nf(2).format(x);
    if (a >= 0.01) return nf(3).format(x);
    return x.toLocaleString('et-EE', { maximumSignificantDigits: 2, maximumFractionDigits: 8 });
  }
  const pct = (r, d = 0) => (r === null || r === undefined || !Number.isFinite(r) ? '–' : `${r > 0 ? '+' : ''}${nf(d).format(r * 100)} %`);
  const sgn = (x) => (x === null || x === undefined || !Number.isFinite(x) ? '–' : `${x > 0 ? '+' : ''}${fmt(x)}`);
  const pfmt = (p) => (p === null || p === undefined ? '–' : p < 0.001 ? '< 0,001' : nf(3).format(p));
  function niceTicks(lo, hi, n = 5) {
    if (!(hi > lo)) { hi = lo + 1; }
    const span = hi - lo, raw = span / n, mag = 10 ** Math.floor(Math.log10(raw));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) || raw;
    const a = Math.floor(lo / step) * step, b = Math.ceil(hi / step) * step, t = [];
    for (let v = a; v <= b + step / 2; v += step) t.push(Math.abs(v) < step * 1e-9 ? 0 : +v.toPrecision(12));
    return { ticks: t, lo: t[0], hi: t[t.length - 1] };
  }
  const cssVar = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  function hex(c) { const m = /^#?([0-9a-f]{6})$/i.exec(c); const v = parseInt(m ? m[1] : '808080', 16); return [(v >> 16) & 255, (v >> 8) & 255, v & 255]; }
  function mixHex(a, b, t) { const A = hex(a), B = hex(b); return `rgb(${A.map((x, i) => Math.round(x + (B[i] - x) * t)).join(',')})`; }
  function lum(rgb) { const [r, g, b] = rgb.match(/\d+/g).map(Number).map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; }

  /* ---------- tooltip ---------- */
  const tip = $('#tip');
  function tipShow(build, ev, anchor) {
    tip.replaceChildren();
    build(tip);
    tip.style.display = 'block';
    const r = tip.getBoundingClientRect();
    let x, y;
    if (ev && ev.clientX !== undefined && ev.type !== 'focus') { x = ev.clientX + 14; y = ev.clientY + 14; } else { const b = anchor.getBoundingClientRect(); x = b.left + b.width / 2; y = b.bottom + 6; }
    x = Math.max(8, Math.min(x, innerWidth - r.width - 8)); y = Math.max(8, Math.min(y, innerHeight - r.height - 8));
    tip.style.left = `${x}px`; tip.style.top = `${y}px`;
  }
  const tipHide = () => { tip.style.display = 'none'; };
  function tipOn(node, build) {
    node.addEventListener('pointermove', (e) => tipShow(build, e, node));
    node.addEventListener('pointerleave', tipHide);
    node.addEventListener('focus', (e) => tipShow(build, e, node));
    node.addEventListener('blur', tipHide);
  }
  function tl(parent, cls, text) { return h('div', { class: cls }, parent, text); }

  /* ---------- andmed ---------- */
  let D; // {meta, P, L, K, byPair, byCell}
  async function load() {
    const raw = window.__OKS__ || Object.fromEntries(await Promise.all(['meta', 'paarid', 'lahtrid', 'klassid', 'jaotused', 'kaasnev', 'tendus', 'nouded', 'algklassid', 'segumudel', 'vordlus'].map(async (n) => {
      try { const r = await fetch(`data/${n}.json`); return [n, r.ok ? await r.json() : null]; } catch { return [n, null]; }
    })));
    const meta = raw.meta;
    const obj = (rows, cols) => rows.map((r) => Object.fromEntries(cols.map((c, i) => [c, r[i]])));
    const P = obj(raw.paarid, meta.paarid_veerud), L = obj(raw.lahtrid, meta.lahtrid_veerud), K = obj(raw.klassid, meta.klassid_veerud);
    const byPair = new Map(P.map((r) => [`${r.layer_id}|${r.unit_code}|${r.pair}`, r]));
    const byCell = new Map(L.map((r) => [`${r.layer_id}|${r.unit_code}|${r.state}`, r]));
    const classMeta = new Map(meta.klassid.map((c) => [c.kood, c]));
    const kByLayer = new Map();
    for (const r of K) { if (!kByLayer.has(r.layer_id)) kByLayer.set(r.layer_id, []); kByLayer.get(r.layer_id).push(r); }
    const dist = new Map(); const distSpec = (raw.jaotused && raw.jaotused.spec) || {};
    for (const [l, u, st, shares, zero] of (raw.jaotused ? raw.jaotused.rows : [])) dist.set(`${l}|${u}|${st}`, { shares, zero });
    // metoodika v2: mediaan algse seisundiklassi kaupa ja segumudeli võrdlus (madalama lahutusvõimega kihid)
    const alg = new Map();
    for (const [l, u, k, st, n, mean, median, mnz] of raw.algklassid || []) { const key = `${l}|${u}`; if (!alg.has(key)) alg.set(key, []); alg.get(key).push({ k, st, n, mean, median, mnz }); }
    const seg = new Map((raw.segumudel || []).map(([l, u, p, d, lo, hi, q]) => [`${l}|${u}|${p}`, { d, lo, hi, q }]));
    D = { meta, P, L, K, byPair, byCell, classMeta, kByLayer, dist, distSpec, alg, seg };
    D.K = raw.kaasnev || null; D.T = raw.tendus || null; D.N = raw.nouded || null; D.V = raw.vordlus || null;
  }

  /* ---------- olek ---------- */
  const S = {
    sec: 'avaleht', tab: 'ulevaade', level: 'okosusteem', ecos: new Set(), alamSel: new Set(), alamN: 12,
    groups: new Set(), props: new Set(), layers: new Set(), pair: 2, est: 'm', sig: 'all', minRel: 0,
    detail: { layer: 0, unit: 0 }, profUnit: 0, sort: { col: 'rel', dir: -1 },
    dmode: 'over', dzero: false, lunit: -1, lsort: 'grupp', lstack: true, lzero: false, hval: 'rel', lvnz: false,
  };
  const eco = (u) => D.meta.uhikud[u].eco;
  const unitArea = (u) => D.meta.uhikud[u].pind.reduce((a, b) => a + (b || 0), 0);

  function visLayers() {
    return D.meta.teenused.map((t, i) => ({ t, i })).filter(({ t }) => S.groups.has(t.grupp) && S.props.has(t.omadus || 'muu') && S.layers.has(t.id));
  }
  function visUnits() {
    const all = D.meta.uhikud.map((u, i) => ({ u, i })).filter(({ u }) => S.ecos.has(u.eco) && u.tase === S.level);
    if (S.level === 'okosusteem') return all.map((x) => x.i);
    let sel = all;
    if (S.alamSel.size) sel = all.filter(({ i }) => S.alamSel.has(i));
    else sel = [...all].sort((a, b) => unitArea(b.i) - unitArea(a.i)).slice(0, S.alamN);
    return sel.sort((a, b) => a.u.eco - b.u.eco || unitArea(b.i) - unitArea(a.i)).map((x) => x.i);
  }
  /** Hinnang (metoodika v2: mediaanide põhjal); k = 'm' paaritatud, 'u' paaritamata. */
  const has = (v) => v !== null && v !== undefined && Number.isFinite(v);
  function estOf(r, k) {
    if (!r) return null;
    return k === 'm'
      ? { d: r.delta_m_med, rel: r.rel_m_med, lo: r.ci_m_med_lo, hi: r.ci_m_med_hi, p: r.p_m_med, q: r.q_m_med, sig: !!r.oluline_m_med, ok: !!r.enough_m && has(r.delta_m_med) }
      : { d: r.delta_u_med, rel: r.rel_u_med, lo: r.ci_u_med_lo, hi: r.ci_u_med_hi, p: r.p_u_med, q: r.q_u_med, sig: !!r.oluline_u_med, ok: !!r.enough_u && has(r.delta_u_med) };
  }
  const est = (r) => estOf(r, S.est);
  function passes(r) {
    const e = est(r);
    if (!e || !e.ok) return false;
    if (S.sig === 'sig' && !e.sig) return false;
    if (S.sig === 'both' && !r.kooskolas_med) return false;
    if (S.minRel > 0 && !(e.rel !== null && Math.abs(e.rel) >= S.minRel / 100)) return false;
    return true;
  }
  const pairsSel = () => (S.pair === '*' ? [0, 1, 2] : [S.pair]);
  const filtersActive = () => S.sig !== 'all' || S.minRel > 0;

  /* ---------- filtririda ---------- */

  /* ---------- filtrite selgitused (info-nupud) ---------- */
  const INFO = {
    tase: ['Tase', ['Ökosüsteem: neli suurt rühma (rohumaad, sood, metsad, põllumaad). Rannikud ning asustus ja muu on baaskaardil „seisundita” ja analüüsis puuduvad.', 'Alamökosüsteem: täpsem baaskaardi tüüp (nt Salumets, 6410 sinihelmikaniidud). Lehel on alamökosüsteemid, millel on vähemalt kaks seisundit.']],
    okosusteem: ['Ökosüsteem', ['Piirab, milliste ökosüsteemide tulemused näidatakse. Algsed seisundiklassid (A–F) on ökosüsteemiti erinevad, seepärast võrreldakse seisundeid alati ühe ökosüsteemi sees.']],
    alam: ['Alamökosüsteem', ['Vali konkreetsed alamökosüsteemid. Kui valikut pole, näidatakse valitud ökosüsteemide suurima pindalaga alamökosüsteeme (arvu määrab „Kui valikut pole: suurimaid”).', 'Pindala (km²) on kolme seisundi summa baaskaardil.']],
    alamN: ['Kui valikut pole: suurimaid', ['Mitu suurima pindalaga alamökosüsteemi kuvatakse, kui sa neid ise ei vali.']],
    grupp: ['Teenusegrupp', ['ELME kihitabeli teemarühm (nt Loodusannid, Puhverdavad teenused). Piirab, milliseid teenuseid näidatakse.']],
    omadus: ['Omadus', ['biofüüsikaline: väärtus füüsikalistes ühikutes (nt t C/ha, kg/ha).', 'rahaline: rahaline hinnang (EUR/ha).', 'muu: indeks või skoor (nt elupaikade säilitamine 0–10).', 'Allikas: ametlik kihitabel (veerg properties).']],
    teenus: ['Teenus', ['Valik analüüsitud teenustest (kihitabelis eval = TRUE). Mõnel teenusel on tulemus ainult teatud ökosüsteemides (nt metsa puitse biomassi süsinik ainult metsades).', 'Ühik on kihitabelist; kus tabel ühikut ei nimeta, on see tühi.']],
    paar: ['Seisundipaar', ['Mida võrreldakse: halvem → parem seisund. Muutus Δ = parema seisundi mediaan − halvema seisundi mediaan; suhteline muutus = Δ jagatud halvema seisundi mediaaniga (puudub, kui see mediaan on 0).', 'Seisundid on ühtlustatud kolmeks klassiks (vilets, keskmine, hea); need tulevad ökosüsteemiti erinevatest algklassidest A–F.', 'Kuumkaart kasutab valitud paari (valikul „kõik” paari vilets → hea); tabel näitab valitud paari või kõiki kolme; profiil näitab alati paari vilets → hea.']],
    hinnang: ['Hinnang: paaritatud ja paaritamata', ['Paaritatud (soovitatav): võrdleb seisundite mediaane samas 1 km plokis ja samas alamökosüsteemis (kummaski vähemalt 1 ha). Nii ei sega asukoht (mullastik, kliima) ega alamökosüsteemide erinev koosseis. Ökosüsteemi tulemus on kõigi selliste plokkide erinevuste kaalutud keskmine.', 'Paaritamata: kõigi pikslite mediaanide vahe valitud seisundite vahel. Kasutab kõiki andmeid, kuid kui nt „hea” esineb teistes piirkondades või alamökosüsteemides kui „vilets”, läheb see erinevus muutusesse (ökosüsteemi tasemel on see toorhinnang).', 'Kui hinnangud lähevad lahku (eriti vastupidise märgiga), mõjutab tulemust asukoht või koosseis.']],
    olulisus: ['Olulisus', ['oluline: FDR-korrigeeritud q < 0,05. Olulisus tuleb 10 × 10 km klastrite bootstrapist (arvestab ruumilist sõltuvust) ja Benjamini–Hochbergi mitmese testimise parandusest. Hinnang vajab vähemalt 20 paari (paaritamata: plokki) ja 5 klastrit.', 'oluline mõlemal hinnangul: nii paaritatud kui paaritamata hinnang on olulised ja sama märgiga.', 'Statistiline olulisus ei tähenda, et muutus on suur; suuruse piiramiseks kasuta filtrit „Min |muutus|”.']],
    minrel: ['Min |muutus|', ['Peidab hinnangud, mille suhteline muutus (% halvema seisundi mediaanist) on absoluutväärtuselt valitud lävest väiksem. 0 % = kõik. Praktilise tähtsuse piiri valid sina; seda ei ole ette seatud.']],
  };
  let infoKey = null;
  function renderInfo() {
    const box = $('#infopanel'); if (!box) return;
    box.replaceChildren();
    if (!infoKey || !INFO[infoKey]) { box.hidden = true; return; }
    const [title, paras] = INFO[infoKey]; box.hidden = false;
    const x = h('button', { type: 'button', class: 'ghost x', 'aria-label': 'Sulge selgitus' }, box, '×'); x.onclick = () => { infoKey = null; renderInfo(); renderFilters(true); };
    h('h4', {}, box, title); for (const t of paras) h('p', {}, box, t);
  }
  function infoBtn(parent, key, label) {
    const b = h('button', { type: 'button', class: 'info', 'aria-label': `Info: ${label}`, 'aria-expanded': String(infoKey === key), 'aria-controls': 'infopanel' }, parent, 'i');
    b.onclick = (e) => { e.preventDefault(); infoKey = infoKey === key ? null : key; renderInfo(); renderFilters(true); };
    return b;
  }
  function lbl(g, text, key, forId) {
    const l = h(forId ? 'label' : 'span', forId ? { for: forId, class: 'lbl' } : { class: 'lbl' }, g, text);
    if (key) infoBtn(l, key, INFO[key][0]);
    return l;
  }
  function seg(parent, label, opts, get, set, cls, info) {
    const g = h('div', { class: `fgrp ${cls || ''}` }, parent); lbl(g, label, info);
    const s = h('div', { class: 'seg', role: 'group', 'aria-label': label }, g);
    for (const [v, t] of opts) { const b = h('button', { type: 'button', 'aria-pressed': String(get() === v) }, s, t); b.onclick = () => { set(v); renderAll(); }; }
    return g;
  }
  function chips(parent, label, items, setObj, info) {
    const g = h('div', { class: 'fgrp' }, parent); lbl(g, label, info);
    const c = h('div', { class: 'chips' }, g);
    for (const [v, t] of items) { const b = h('button', { type: 'button', class: 'chip', 'aria-pressed': String(setObj.has(v)) }, c, t); b.onclick = () => { setObj.has(v) ? setObj.delete(v) : setObj.add(v); renderAll(); }; }
  }
  function dropdown(parent, label, summary, sections, opts = {}) {
    const g = h('div', { class: 'fgrp' }, parent); lbl(g, label, opts.info);
    const d = h('details', { class: 'dd' }, g); h('summary', { class: 'sel' }, d, summary);
    const p = h('div', { class: 'dd-panel' }, d);
    let q = null;
    if (opts.search) { q = h('input', { type: 'search', placeholder: 'Otsi…', 'aria-label': `${label}: otsi` }, p); }
    const acts = h('div', { class: 'acts' }, p);
    const all = h('button', { type: 'button', class: 'ghost' }, acts, 'Vali kõik'), none = h('button', { type: 'button', class: 'ghost' }, acts, 'Tühjenda');
    const rows = [];
    for (const sec of sections) {
      if (sec.title) h('h4', {}, p, sec.title);
      for (const it of sec.items) {
        const r = h('label', { class: 'row' }, p); const cb = h('input', { type: 'checkbox' }, r); cb.checked = it.get();
        cb.onchange = () => { it.set(cb.checked); renderAll(true); };
        const sp = h('span', {}, r, it.label); if (it.small) h('small', {}, sp, ` ${it.small}`);
        rows.push({ r, cb, it, text: `${it.label} ${it.small || ''}`.toLowerCase() });
      }
    }
    const bulk = (v) => { for (const x of rows) if (x.r.style.display !== 'none') { x.cb.checked = v; x.it.set(v); } renderAll(true); };
    all.onclick = () => bulk(true); none.onclick = () => bulk(false);
    if (q) q.oninput = () => { const s = q.value.trim().toLowerCase(); for (const x of rows) x.r.style.display = x.text.includes(s) ? '' : 'none'; };
    return d;
  }
  const openDD = new Set();
  function renderFilters(keepOpen) {
    const box = $('#filters');
    const opened = keepOpen ? [...box.querySelectorAll('details.dd')].map((d) => d.open) : [];
    const sy = scrollY;
    box.replaceChildren();
    const M = D.meta;
    seg(box, 'Tase', [['okosusteem', 'Ökosüsteem'], ['alam', 'Alamökosüsteem']], () => S.level, (v) => { S.level = v; }, '', 'tase');
    const ecoItems = M.uhikud.filter((u) => u.tase === 'okosusteem').map((u) => [u.kood, u.nimi]);
    chips(box, 'Ökosüsteem', ecoItems, S.ecos, 'okosusteem');
    if (S.level === 'alam') {
      const items = M.uhikud.map((u, i) => ({ u, i })).filter(({ u }) => u.tase === 'alam' && S.ecos.has(u.eco)).sort((a, b) => a.u.eco - b.u.eco || unitArea(b.i) - unitArea(a.i));
      dropdown(box, 'Alamökosüsteem', S.alamSel.size ? `${S.alamSel.size} valitud` : `${Math.min(S.alamN, items.length)} suurimat`,
        [{ items: items.map(({ u, i }) => ({ label: u.nimi, small: `${nf(0).format(unitArea(i))} km²`, get: () => S.alamSel.has(i), set: (v) => (v ? S.alamSel.add(i) : S.alamSel.delete(i)) })) }], { search: true, info: 'alam' });
      const g = h('div', { class: 'fgrp' }, box); lbl(g, 'Kui valikut pole: suurimaid', 'alamN', 'alamN');
      const sel = h('select', { id: 'alamN' }, g);
      for (const n of [6, 12, 20, 40]) { const o = h('option', { value: n }, sel, String(n)); if (n === S.alamN) o.selected = true; }
      sel.onchange = () => { S.alamN = +sel.value; renderAll(); };
    }
    const groups = [...new Set(M.teenused.map((t) => t.grupp))];
    dropdown(box, 'Teenusegrupp', `${S.groups.size}/${groups.length}`, [{ items: groups.map((g) => ({ label: g, get: () => S.groups.has(g), set: (v) => (v ? S.groups.add(g) : S.groups.delete(g)) })) }], { info: 'grupp' });
    chips(box, 'Omadus', [['biofüüsikaline', 'biofüüsikaline'], ['rahaline', 'rahaline'], ['muu', 'muu']], S.props, 'omadus');
    const secs = groups.map((g) => ({ title: g, items: M.teenused.filter((t) => t.grupp === g).map((t) => ({ label: t.nimi, small: t.uhik, get: () => S.layers.has(t.id), set: (v) => (v ? S.layers.add(t.id) : S.layers.delete(t.id)) })) }));
    dropdown(box, 'Teenus', `${S.layers.size}/${M.teenused.length}`, secs, { search: true, info: 'teenus' });
    seg(box, 'Seisundipaar (halvem → parem)', [...M.paarid.map((p, i) => [i, p.replace('→', ' → ')]), ['*', 'kõik']], () => S.pair, (v) => { S.pair = v; }, '', 'paar');
    seg(box, 'Hinnang', [['m', 'Paaritatud'], ['u', 'Paaritamata']], () => S.est, (v) => { S.est = v; }, '', 'hinnang');
    const g = h('div', { class: 'fgrp' }, box); lbl(g, 'Olulisus', 'olulisus', 'sigsel');
    const ss = h('select', { id: 'sigsel' }, g);
    for (const [v, t] of [['all', 'kõik hinnangud'], ['sig', 'oluline (FDR q < 0,05)'], ['both', 'oluline mõlemal hinnangul']]) { const o = h('option', { value: v }, ss, t); if (S.sig === v) o.selected = true; }
    ss.onchange = () => { S.sig = ss.value; renderAll(); };
    const g2 = h('div', { class: 'fgrp' }, box); const l2w = lbl(g2, '', 'minrel', 'minrel'); const l2 = h('span', {}, null, `Min |muutus|: ${S.minRel} %`); l2w.prepend(l2);
    const rg = h('input', { type: 'range', id: 'minrel', min: 0, max: 200, step: 5, value: S.minRel }, g2);
    rg.oninput = () => { l2.textContent = `Min |muutus|: ${rg.value} %`; }; rg.onchange = () => { S.minRel = +rg.value; renderAll(true); };
    const rs = h('button', { type: 'button', class: 'ghost' }, box, 'Lähtesta'); rs.onclick = () => { initState(); renderAll(); };
    h('span', { class: 'count', id: 'count' }, box, '');
    if (keepOpen) box.querySelectorAll('details.dd').forEach((d, i) => { d.open = !!opened[i]; });
    renderInfo();
    scrollTo(0, sy);
  }

  /* ---------- vahekaardid ---------- */
  const TABS = [['ulevaade', 'Kuumkaart'], ['teenus', 'Teenuse detail'], ['profiil', 'Profiil'], ['jaotused', 'Jaotused'], ['kihid', 'Kihtide ülevaade'], ['tabel', 'Tabel']];
  const SECTIONS = [['avaleht', 'Avaleht'], ['tulemused', 'Tulemustabel'], ['stsenaarium', 'Stsenaarium'], ['kvalit', 'Kvalitatiivne'], ['analuus', 'Statistiline analüüs'], ['lahteulesanne', 'Lähteülesande täitmine'], ['vordlus', 'Metoodika võrdlus'], ['meetod', 'Meetod']];
  function renderSections() {
    const n = $('#sections'); n.replaceChildren();
    for (const [k, t] of SECTIONS) { const a = h('a', { href: `#${k}`, class: 'sec', 'aria-current': S.sec === k ? 'page' : null }, n, t); a.onclick = (e) => { e.preventDefault(); navTo(k); }; }
  }
  function renderTabs() {
    const n = $('#tabs'); n.replaceChildren();
    for (const [k, t] of TABS) { const b = h('button', { role: 'tab', type: 'button', 'aria-selected': String(S.tab === k) }, n, t); b.onclick = () => { S.tab = k; renderAll(true); }; }
  }

  /* ---------- Ülevaade: kuumkaart ---------- */
  function divColor(rel, sig) {
    const t = Math.min(1, Math.abs(rel));
    return { fill: mixHex(cssVar('--mid'), cssVar(rel >= 0 ? '--pos' : '--neg'), t), op: sig ? 1 : 0.38 };
  }
  function heatmap(root) {
    const layers = visLayers(), units = visUnits();
    const pair = S.pair === '*' ? 2 : S.pair;
    const rows = [];
    for (const { t, i } of layers) {
      const cells = units.map((u) => D.byPair.get(`${i}|${u}|${pair}`));
      if (!cells.some(Boolean)) continue;
      if (filtersActive() && !cells.some((c) => c && passes(c))) continue;
      rows.push({ t, i, cells });
    }
    const card = h('section', { class: 'card' }, root);
    h('h2', {}, card, `Seisundi muutus: ${D.meta.paarid[pair].replace('→', ' → ')}`);
    h('p', { class: 'sub' }, card, `Värv = teenuse suhteline muutus (parem − halvem seisund, % halvema seisundi mediaanist), hinnang: ${S.est === 'm' ? 'paaritatud (sama 1 km plokk ja alamökosüsteem)' : 'paaritamata (kõik pikslid)'}. Täisvärv = statistiliselt oluline (FDR q < 0,05), kahvatu = ei ole oluline, tühi = andmeid pole või filter välistab. Klõpsa lahtrit või teenuse nime, et avada detail.`);
    const ht = h('div', { class: 'tools' }, card);
    h('span', { class: 'tl' }, ht, 'Lahtris');
    const hs = h('div', { class: 'seg', role: 'group', 'aria-label': 'Mida lahtris näidata' }, ht);
    for (const [v, t] of [['rel', 'Suhteline muutus (%)'], ['abs', 'Muutus kihi ühikus']]) { const b = h('button', { type: 'button', 'aria-pressed': String(S.hval === v) }, hs, t); b.onclick = () => { S.hval = v; renderAll(true); }; }
    if (S.hval === 'abs') h('p', { class: 'note' }, card, 'Lahtris on muutus kihi enda ühikus (biofüüsikaline, nt t C/ha, või rahaline, nt EUR/ha); ühik on rea nime järel. Värv näitab endiselt suhtelist muutust, et eri ühikutega ridu saaks võrrelda.');
    if (S.est === 'u' && S.level === 'okosusteem') h('p', { class: 'warn' }, card, 'Paaritamata hinnang ökosüsteemi tasemel on toorhinnang: seisundiklasside alamökosüsteemide koosseis võib erineda ja see mõjutab tulemust. Soovitatav on paaritatud hinnang.');
    if (!rows.length || !units.length) { h('p', { class: 'empty' }, card, 'Valitud filtritele ei vasta ühtegi tulemust.'); return; }
    const wrapW0 = Math.max(root.clientWidth - 40, 300), labelW = wrapW0 < 700 ? 176 : 360, maxCh = Math.floor(labelW / 6.4), hdrH = S.level === 'alam' ? 150 : 44, rowH = 26, gap = 2;
    const wrapW = Math.max(root.clientWidth - 40, 300);
    const cw = Math.max(S.level === 'alam' ? 54 : 52, Math.min(130, Math.floor((wrapW - labelW) / units.length)));
    const W = labelW + units.length * cw + (S.level === "alam" ? 90 : 10);
    let nGroups = 0, last = null; for (const r of rows) if (r.t.grupp !== last) { nGroups++; last = r.t.grupp; }
    const Hh = hdrH + rows.length * rowH + nGroups * 20 + 10;
    const sc = h('div', { class: 'scroll' }, card);
    const svg = h('svg', { width: W, height: Hh, role: 'group', 'aria-label': 'Kuumkaart: teenused ja ökosüsteemid' }, sc);
    units.forEach((u, j) => {
      const U = D.meta.uhikud[u], x = labelW + j * cw + cw / 2;
      if (S.level === 'alam') h('text', { x, y: hdrH - 6, transform: `rotate(-45 ${x} ${hdrH - 6})`, class: 'lbl' }, svg, U.nimi.length > 34 ? `${U.nimi.slice(0, 33)}…` : U.nimi);
      else h('text', { x, y: hdrH - 10, 'text-anchor': 'middle', class: 'strong' }, svg, U.nimi);
    });
    let y = hdrH; last = null;
    for (const r of rows) {
      if (r.t.grupp !== last) { h('text', { x: 0, y: y + 14, class: 'strong' }, svg, r.t.grupp); y += 20; last = r.t.grupp; }
      const lab = h('g', { class: 'rowlbl', tabindex: 0, role: 'button', 'aria-label': `Ava detail: ${r.t.nimi}` }, svg);
      const unitTxt = r.t.uhik ? ` · ${r.t.uhik.split(' (')[0]}` : '';
      const mark = (r.t.lahutus_markus ? ' ‡' : '') + (r.t.nodata_valja ? ' §' : '') + (r.t.definitsiooniline ? ' †' : '');
      const full = `${r.t.nimi}${unitTxt}${mark}`;
      const keep = Math.max(8, maxCh - unitTxt.length - mark.length - 1);
      const nm = full.length > maxCh ? `${r.t.nimi.slice(0, keep)}…${unitTxt}${mark}` : full;
      h('text', { x: 8, y: y + rowH / 2 + 4, class: 'lbl' }, lab, nm);
      h('title', {}, lab, `${r.t.pealkiri || r.t.nimi} (${r.t.uhik || 'ühik dokumenteerimata'})`);
      const go = () => { S.detail.layer = r.i; const u0 = units[0]; S.detail.unit = r.cells.findIndex(Boolean) >= 0 ? units[r.cells.findIndex(Boolean)] : u0; S.tab = 'teenus'; renderAll(true); scrollTo(0, 0); };
      lab.onclick = go; lab.onkeydown = (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } };
      r.cells.forEach((c, j) => {
        const x = labelW + j * cw;
        const e = est(c);
        const g = h('g', { class: 'cell', tabindex: c ? 0 : -1 }, svg);
        const ok = c && e.ok && passes(c);
        let fill = 'none', op = 1, txt = '', tc = cssVar('--ink-2');
        if (ok) {
          // kui halvema seisundi mediaan on 0, suhtelist muutust ei ole: värv näitab siis ainult suunda
          const hasRel = has(e.rel), cr = hasRel ? e.rel : Math.sign(e.d) * 0.5;
          const d = divColor(cr, e.sig); fill = d.fill; op = d.op;
          txt = S.hval === 'abs' ? sgn(e.d) : hasRel ? pct(e.rel) : 'Δ';
          tc = lum(fill) < 0.4 ? '#ffffff' : '#0b0b0b'; if (!e.sig) tc = cssVar('--ink');
        }
        h('rect', { class: 'bg', x: x + 1, y: y + 1, width: cw - gap, height: rowH - gap, rx: 3, fill, 'fill-opacity': op, stroke: ok ? 'none' : cssVar('--line'), 'stroke-dasharray': ok ? null : '2 2' }, g);
        if (ok && cw >= 46) h('text', { x: x + cw / 2, y: y + rowH / 2 + 4, 'text-anchor': 'middle', fill: tc, style: `fill:${tc};font-weight:${e.sig ? 600 : 400};font-size:11px` }, g, txt);
        if (ok && c) { const eta = D.meta.teenused[r.i].eta2[String(eco(units[j]))]; if (eta && eta[0] >= 0.9) h('polygon', { points: `${x + cw - 9},${y + 2} ${x + cw - 2},${y + 2} ${x + cw - 2},${y + 9}`, fill: cssVar('--ink'), 'fill-opacity': 0.55 }, g); }
        if (c) {
          g.setAttribute('role', 'img'); g.setAttribute('aria-label', `${r.t.nimi}, ${D.meta.uhikud[units[j]].nimi}: ${ok ? txt : 'pole hinnatav või välja filtreeritud'}`);
          tipOn(g, (t) => pairTip(t, c));
          g.onclick = () => { S.detail.layer = r.i; S.detail.unit = units[j]; S.tab = 'teenus'; renderAll(true); scrollTo(0, 0); };
          g.onkeydown = (ev) => { if (ev.key === 'Enter') g.onclick(); };
        }
      });
      y += rowH;
    }
    const lg = h('ul', { class: 'legend' }, card);
    const li1 = h('li', {}, lg); h('span', { class: 'ramp' }, li1); h('span', {}, li1, '−100 % … 0 … +100 % (oranž = väärtus väheneb, sinine = väärtus kasvab; järsemad muutused küllastuvad). „Δ“: halvema seisundi mediaan on 0, värv näitab ainult suunda');
    const li3 = h('li', {}, lg); h('span', {}, li3, '‡ = madalama lahutusvõimega kiht (930 m / 1 km), viidud 10 m lahutusvõimele: seisundite erinevus tuleb ainult algsete ruutude vahelistest erinevustest');
    const li5 = h('li', {}, lg); h('span', {}, li5, '§ = erandkiht: kihi puuduvad andmed on valimist välja jäetud (mitte loetud nulliks)');
    const li4 = h('li', {}, lg); h('span', {}, li4, '† = seos seisundiga on osaliselt definitsiooniline (kihi väärtus on tuletatud seisundiklassist; vt teenuse detail)');
    const li2 = h('li', {}, lg); h('svg', { width: 12, height: 12 }, li2).append(h('polygon', { points: '12,0 12,10 2,0', fill: cssVar('--ink'), 'fill-opacity': 0.55 })); h('span', {}, li2, 'nurgamärk: ≥ 90 % kihi dispersioonist on baaskaardi klassi tabelväärtus (mudelipõhine; seisundi mõju osaliselt definitsiooniline)');
    h('p', { class: 'note' }, card, 'Suund pole hinnang: näiteks erosiooni ärakandel tähendab positiivne muutus suuremat ärakannet, kliimaregulatsiooni indeksil tähendab väiksem väärtus ühtlasemat temperatuuri. Vt teenuse detaili.');
  }

  function pairTip(t, c) {
    const T = D.meta.teenused[c.layer_id], U = D.meta.uhikud[c.unit_code], e = est(c), eta = T.eta2[String(U.eco)];
    tl(t, 'm', `${T.nimi}`); tl(t, 'm', `${U.nimi} · ${D.meta.paarid[c.pair].replace('→', ' → ')}`);
    if (!e || !e.ok) { tl(t, 'm', 'Pole piisavalt andmeid selle hinnangu jaoks'); return; }
    tl(t, 'v', `${pct(e.rel, 1)}  (${sgn(e.d)} ${T.uhik || ''})`);
    tl(t, 'm', `95 % CI: ${sgn(e.lo)} … ${sgn(e.hi)}`);
    tl(t, 'm', `${S.est === 'm' ? 'paaritatud' : 'paaritamata'} · p ${pfmt(e.p)} · q ${pfmt(e.q)} · ${e.sig ? 'oluline' : 'ei ole oluline'}`);
    tl(t, 'm', `mediaan ${fmt(c.median_a)} → ${fmt(c.median_b)} · keskmine ${fmt(c.mean_a)} → ${fmt(c.mean_b)}`);
    if (S.est === 'm') tl(t, 'm', `${nf(0).format(c.n_strata)} paari (plokk × alamökosüsteem), ${c.n_clusters_m} klastrit`);
    else tl(t, 'm', `${nf(0).format(c.blocks_a)} / ${nf(0).format(c.blocks_b)} plokki`);
    if (eta) tl(t, 'm', `η² (klass → väärtus): ${nf(2).format(eta[0])}`);
  }

  /* ---------- Teenuse detail ---------- */
  function stateColor(s) { return cssVar(`--st-${s + 1}`); }
  function yScale(lo, hi, H, m) { return (v) => m.t + (H - m.t - m.b) * (1 - (v - lo) / (hi - lo || 1)); }
  function detail(root) {
    const M = D.meta, li = S.detail.layer, ui = S.detail.unit, T = M.teenused[li], U = M.uhikud[ui];
    const card = h('section', { class: 'card' }, root);
    const ctl = h('div', { class: 'frow' }, card);
    const g1 = h('div', { class: 'fgrp wide' }, ctl); h('label', { for: 'dl' }, g1, 'Teenus');
    const sl = h('select', { id: 'dl' }, g1);
    for (const [i, t] of M.teenused.entries()) { const o = h('option', { value: i }, sl, `${t.grupp} · ${t.nimi}${t.uhik ? ` (${t.uhik})` : ''}`); if (i === li) o.selected = true; }
    sl.onchange = () => { S.detail.layer = +sl.value; renderAll(true); };
    const g2 = h('div', { class: 'fgrp' }, ctl); h('label', { for: 'du' }, g2, 'Ökosüsteem / alamökosüsteem');
    const su = h('select', { id: 'du' }, g2);
    const us = M.uhikud.map((u, i) => ({ u, i })).filter(({ i }) => D.byCell.has(`${li}|${i}|0`) || D.byCell.has(`${li}|${i}|1`) || D.byCell.has(`${li}|${i}|2`));
    for (const { u, i } of us) { const o = h('option', { value: i }, su, `${u.tase === 'okosusteem' ? '▪ ' : '   '}${u.nimi}`); if (i === ui) o.selected = true; }
    if (!us.some(({ i }) => i === ui) && us.length) S.detail.unit = us[0].i;
    su.onchange = () => { S.detail.unit = +su.value; renderAll(true); };
    h('h2', {}, card, T.nimi);
    if (T.pealkiri && T.pealkiri !== T.nimi) h('p', { class: 'sub' }, card, T.pealkiri);
    const b = h('div', { class: 'badges' }, card);
    for (const x of [T.grupp, T.omadus, T.tuup && `tüüp: ${T.tuup}`, T.uhik && `ühik: ${T.uhik}`, T.res && `${T.res} m`, T.aasta && `${T.aasta}`, T.allikas, T.meetod && `meetod: ${T.meetod}`, T.nodata_valja && '§ erandkiht'].filter(Boolean)) h('span', { class: 'badge' }, b, String(x));
    if (T.lahutus_markus) h('p', { class: 'warn' }, card, `‡ ${T.lahutus_markus}`);
    if (T.nodata_valja) h('p', { class: 'warn' }, card, '§ Erandkiht: selle kihi puuduvad andmed (NoData) on valimist välja jäetud, sest need tähendavad puuduvat hinnangut, mitte teenuse puudumist. Teistes kihtides loetakse puuduvad andmed nulliks.');
    if (T.markus) h('p', { class: 'warn' }, card, T.markus);
    if (T.tabeli_markus) h('p', { class: 'warn' }, card, `Kihitabeli märkus: ${T.tabeli_markus}`);
    const eta = T.eta2[String(U.eco)];
    if (eta && eta[0] >= 0.9) h('p', { class: 'warn' }, card, `Mudelipõhisuse hoiatus: ${nf(0).format(eta[0] * 100)} % selle kihi dispersioonist ${M.uhikud.find((u) => u.tase === 'okosusteem' && u.eco === U.eco).nimi.toLowerCase()} sees on seletatav baaskaardi klassiga (η² = ${nf(2).format(eta[0])}; seisundi osa alamökosüsteemi sees η² = ${nf(2).format(eta[2])}). Kihi väärtus sõltub suures osas klassi tabelväärtusest, mitte iseseisvast mõõtmisest; muutus seisundi vahel on seega osaliselt definitsiooniline.`);
    if (T.kirjeldus) { const d = h('details', {}, card); h('summary', {}, d, 'Kihi kirjeldus (ametlik kihitabel)'); h('p', { class: 'note' }, d, T.kirjeldus); }
    h('h3', {}, card, `${U.nimi}: pindala seisundi kaupa`);
    h('p', { class: 'note' }, card, M.seisundid.map((s, i) => `${s}: ${nf(0).format(U.pind[i] || 0)} km²`).join(' · '));

    const grid = h('div', { class: 'grid2' }, root);
    const dcard = h('section', { class: 'card wide' }, grid);
    const cards = [0, 1, 2, 3].map(() => h('section', { class: 'card' }, grid));
    const tcard = h('section', { class: 'card' }, root);
    distChart(dcard, li, ui);
    levelsChart(cards[0], li, ui);
    deltaChart(cards[1], li, ui, 'rel');
    deltaChart(cards[2], li, ui, 'abs');
    classChart(cards[3], li, ui);
    pairTable(tcard, li, ui);
    segTable(tcard, li, ui);
  }
  /** Segumudeli võrdlus (keskmisel põhinev, uuriv) madalama lahutusvõimega kihtidele ökosüsteemi tasemel. */
  function segTable(card, li, ui) {
    const rows = [0, 1, 2].map((p) => [p, D.seg.get(`${li}|${ui}|${p}`)]).filter(([, r]) => r);
    if (!rows.length) return;
    h('h3', {}, card, 'Võrdluseks: segumudel');
    h('p', { class: 'note' }, card, 'Segumudel hindab kihi väärtust ruudu ökosüsteemide ja seisundite pindalaosade järgi (keskmisel põhinev, uuriv). See on alles võrdluseks madalama lahutusvõimega kihtidele.');
    const sc = h('div', { class: 'scroll' }, card), t = h('table', { class: 'data' }, sc), hd = h('tr', {}, h('thead', {}, t));
    for (const c of ['Seisundipaar', 'Δ (segumudel)', '95 % CI', 'q (FDR)']) h('th', {}, hd, c);
    const tb = h('tbody', {}, t);
    for (const [p, r] of rows) { const tr = h('tr', {}, tb); h('td', {}, tr, D.meta.paarid[p].replace('→', ' → ')); h('td', {}, tr, sgn(r.d)); h('td', {}, tr, `${sgn(r.lo)} … ${sgn(r.hi)}`); h('td', {}, tr, pfmt(r.q)); }
  }


  /* ---------- Jaotused (pikslitaseme histogrammid) ---------- */
  const SHAPE = ['dot', '', 'dia']; // vilets = ring, keskmine = ruut, hea = romb (värvi ei kasutata ainsa eristajana)
  function swatch(parent, s) { return h('span', { class: `sw ${SHAPE[s]} s${s + 1}` }, parent); }
  const stateInk = (s) => cssVar(`--st-${s + 1}i`);
  function stateLegend(parent) {
    const lg = h('ul', { class: 'legend' }, parent);
    D.meta.seisundid.forEach((s, i) => { const l = h('li', {}, lg); swatch(l, i); h('span', {}, l, s); });
    return lg;
  }
  function binOf(spec, x) {
    if (spec.kind === 'lut') return spec.edges.indexOf(x);
    const e = spec.edges, lo = e[0], hi = e[spec.nbins];
    if (x < lo) return 0;
    if (x >= hi) return spec.nbins + 1;
    const t = spec.kind === 'sqrt' ? (Math.sqrt(Math.max(x, 0)) - Math.sqrt(lo)) / (Math.sqrt(hi) - Math.sqrt(lo)) : (x - lo) / (hi - lo);
    return Math.min(spec.nbins, Math.max(1, Math.floor(t * spec.nbins) + 1));
  }
  /** Seisundite jaotused (osakaalud 0..1); noZero = täpsed nullid välja ja ülejäänu uuesti 100 %-ks. */
  function distFor(li, ui, noZero) {
    const spec = D.distSpec[li];
    if (!spec) return null;
    const zb = binOf(spec, 0);
    const series = [0, 1, 2].map((st) => {
      const d = D.dist.get(`${li}|${ui}|${st}`);
      if (!d) return null;
      let p = d.shares.map((v) => v / 10000);
      const zero = d.zero / 10000;
      if (noZero && zb >= 0 && zero > 0) {
        p = p.slice(); p[zb] = Math.max(0, p[zb] - zero);
        const s = p.reduce((a, b) => a + b, 0); if (s > 0) p = p.map((v) => v / s);
      }
      return { p, zero, noZero: !!noZero, cell: D.byCell.get(`${li}|${ui}|${st}`) || null };
    });
    return series.some(Boolean) ? { spec, series, zb } : null;
  }
  /** Täpne pikslimediaan (tulemustabelist); ilma nullideta vaates nullist erinevate pikslite mediaan. */
  function exactMed(d) {
    if (!d || !d.cell) return null;
    const v = d.noZero ? d.cell.median_nz : d.cell.median;
    return has(v) ? v : null;
  }
  /** Kvantiil vahemike täpsusega (lineaarne interpolatsioon vahemiku sees; ruutjuure skaalal √x-s). */
  function quantile(spec, p, q) {
    let c = 0;
    for (let i = 0; i < p.length; i++) {
      const nc = c + p[i];
      if (nc >= q - 1e-12 && p[i] > 0) {
        if (spec.kind === 'lut') return i < spec.edges.length ? spec.edges[i] : null;
        const e = spec.edges;
        if (i === 0) return e[0];
        if (i === spec.nbins + 1) return e[spec.nbins];
        const f = (q - c) / p[i], a = e[i - 1], b = e[i];
        return spec.kind === 'sqrt' ? (Math.sqrt(a) + f * (Math.sqrt(b) - Math.sqrt(a))) ** 2 : a + f * (b - a);
      }
      c = nc;
    }
    return null;
  }
  /** Väärtuse asukoht x-teljel vahemike ühikutes (0 .. n_bins). */
  function valuePos(spec, v) {
    const n = spec.n_bins;
    if (spec.kind === 'lut') {
      const e = spec.edges; let j = 0; while (j + 1 < e.length && e[j + 1] <= v) j++;
      const f = j + 1 < e.length ? (v - e[j]) / (e[j + 1] - e[j]) : 0;
      return Math.max(0.5, Math.min(e.length - 0.5, j + 0.5 + Math.max(0, Math.min(1, f))));
    }
    const e = spec.edges, lo = e[0], hi = e[spec.nbins];
    const t = spec.kind === 'sqrt' ? (Math.sqrt(Math.max(v, 0)) - Math.sqrt(lo)) / (Math.sqrt(hi) - Math.sqrt(lo)) : (v - lo) / (hi - lo);
    return Math.max(0, Math.min(n, 1 + t * spec.nbins));
  }
  /** „Ümmargused“ teljesildid (mitte vahemike servad). */
  function xTicks(spec, maxN = 6) {
    if (spec.kind === 'lut') {
      const e = spec.edges, k = Math.ceil(e.length / maxN);
      return e.map((v, j) => ({ pos: j + 0.5, label: fmt(v) })).filter((_, j) => j % k === 0);
    }
    const lo = spec.edges[0], hi = spec.edges[spec.nbins], nt = niceTicks(lo, hi, maxN);
    return nt.ticks.filter((v) => v >= lo - 1e-9 && v <= hi + 1e-9).map((v) => ({ pos: valuePos(spec, v), label: fmt(v) }));
  }
  function binLabels(spec) {
    const f = (v) => fmt(v);
    if (spec.kind === 'lut') return [...spec.edges.map(f), 'muu'];
    const e = spec.edges, out = [`< ${f(e[0])}`];
    for (let i = 0; i < spec.nbins; i++) out.push(`${f(e[i])} … ${f(e[i + 1])}`);
    out.push(`≥ ${f(e[spec.nbins])}`);
    return out;
  }
  const isBars = (spec) => spec.kind === 'lut' && spec.n_bins <= 12;
  function stepPath(p, x, y) {
    let d = `M${x(0)},${y(0)}`;
    p.forEach((v, i) => { d += ` L${x(i)},${y(v)} L${x(i + 1)},${y(v)}`; });
    return `${d} L${x(p.length)},${y(0)}`;
  }
  function stepLine(p, x, y) { return `M${x(0)},${y(p[0])} ` + p.map((v, i) => `L${x(i)},${y(v)} L${x(i + 1)},${y(v)}`).join(' '); }
  function medianMark(svg, x, y0, spec, d, st, len) {
    const med = exactMed(d); if (med === null) return;
    const cx = x(valuePos(spec, med)), ink = stateInk(st);
    if (len) h('line', { x1: cx, x2: cx, y1: y0, y2: y0 - len, stroke: ink, 'stroke-width': 1.5, 'stroke-dasharray': '4 3', opacity: 0.8 }, svg);
    h('polygon', { points: `${cx - 5.5},${y0 + 9} ${cx},${y0 + 1} ${cx + 5.5},${y0 + 9}`, fill: ink, stroke: cssVar('--surface'), 'stroke-width': 1.2 }, svg);
  }
  function xAxis(svg, spec, x, y0, W, m, unit) {
    h('line', { x1: m.l, x2: W - m.r, y1: y0, y2: y0, class: 'axis' }, svg);
    for (const t of xTicks(spec)) { h('line', { x1: x(t.pos), x2: x(t.pos), y1: y0, y2: y0 + 4, class: 'axis' }, svg); h('text', { x: x(t.pos), y: y0 + 22, 'text-anchor': 'middle' }, svg, t.label); }
    if (spec.kind !== 'lut') {
      h('text', { x: x(0.5), y: y0 + 22, 'text-anchor': 'middle', class: 'panel-lbl' }, svg, '‹');
      h('text', { x: x(spec.n_bins - 0.5), y: y0 + 22, 'text-anchor': 'middle', class: 'panel-lbl' }, svg, '›');
    }
    h('text', { x: m.l + (W - m.l - m.r) / 2, y: y0 + 42, 'text-anchor': 'middle' }, svg, unit || 'väärtus');
  }
  function distStats(card, c) {
    const { spec, series, T, noZero } = c, unit = (T.uhik || '').split(' (')[0];
    const box = h('div', { class: 'stats' }, card);
    series.forEach((d, st) => {
      if (!d) return;
      const med = exactMed(d), q1 = quantile(spec, d.p, 0.25), q3 = quantile(spec, d.p, 0.75);
      const s = h('div', { class: `stat s${st + 1}` }, box);
      const nm = h('div', { class: 'nm' }, s); swatch(nm, st); h('span', {}, nm, D.meta.seisundid[st]);
      const big = h('div', { class: 'big' }, s, med === null ? '–' : fmt(med)); h('small', {}, big, `mediaan${noZero ? ' (ilma nullideta)' : ''} ${unit}`);
      h('div', { class: 'sm' }, s, `keskmine${noZero ? ' (kõik pikslid)' : ''} ${fmt(d.cell ? d.cell.mean : null)} · 25–75 % (ligikaudne): ${fmt(q1)} … ${fmt(q3)}`);
      if (d.zero >= 0.01) h('div', { class: 'sm' }, s, `täpselt 0: ${nf(0).format(d.zero * 100)} % pikslitest`);
    });
  }
  function chartOver(parent, c) {
    const { spec, series, W, T } = c, n = spec.n_bins, H = 300, m = { l: 52, r: 14, t: 14, b: 56 };
    const top = Math.max(...series.filter(Boolean).flatMap((d) => d.p)) * 100;
    const tk = niceTicks(0, top * 1.08, 5), y = (v) => m.t + (H - m.t - m.b) * (1 - v / (tk.hi || 1)), x = (i) => m.l + (W - m.l - m.r) * (i / n);
    const sc = h('div', { class: 'scroll' }, parent);
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': `${T.nimi}: väärtuste jaotus seisundi kaupa, kattuvad kõverad` }, sc);
    for (const v of tk.ticks) { h('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: 'grid' }, svg); h('text', { x: m.l - 6, y: y(v) + 4, 'text-anchor': 'end' }, svg, `${nf(0).format(v)} %`); }
    series.forEach((d, st) => {
      if (!d) return; const p = d.p.map((v) => v * 100);
      if (isBars(spec)) {
        const bw = (W - m.l - m.r) / n, w = Math.min(20, (bw - 6) / 3);
        p.forEach((v, i) => { if (v > 0) h('rect', { x: x(i) + bw / 2 + (st - 1) * (w + 2) - w / 2, y: y(v), width: w, height: y(0) - y(v), rx: 2, fill: stateColor(st) }, svg); });
      } else {
        h('path', { d: stepPath(p, x, y), fill: stateColor(st), 'fill-opacity': 0.3, stroke: 'none' }, svg);
        h('path', { d: stepLine(p, x, y), fill: 'none', stroke: stateInk(st), 'stroke-width': 2, 'stroke-linejoin': 'round' }, svg);
      }
    });
    xAxis(svg, spec, x, y(0), W, m, T.uhik);
    series.forEach((d, st) => { if (d) medianMark(svg, x, y(0), spec, d, st, y(0) - y(tk.hi)); });
    hoverBins(svg, c, x, m, H);
  }
  function hoverBins(svg, c, x, m, H) {
    const { spec, series, T } = c, labels = binLabels(spec), n = spec.n_bins;
    for (let i = 0; i < n; i++) {
      const r = h('rect', { x: x(i), y: m.t, width: x(i + 1) - x(i), height: H - m.t - m.b, fill: 'transparent' }, svg);
      tipOn(r, (t) => { tl(t, 'm', `${T.nimi} · ${labels[i]} ${T.uhik || ''}`); series.forEach((d, st) => { if (d) { const row = tl(t, 'v', `${nf(1).format(d.p[i] * 100)} %`); h('span', { class: 'm' }, row, `  ${D.meta.seisundid[st]}`); } }); });
    }
  }
  function chartSplit(parent, c) {
    const { spec, series, W, T } = c, n = spec.n_bins, act = series.map((d, st) => ({ d, st })).filter((o) => o.d);
    const ph = 88, gap = 22, m = { l: 52, r: 14, t: 8, b: 56 }, H = m.t + act.length * (ph + gap) - gap + m.b;
    const top = Math.max(...act.flatMap((o) => o.d.p)) * 100, tk = niceTicks(0, top * 1.08, 2), x = (i) => m.l + (W - m.l - m.r) * (i / n);
    const sc = h('div', { class: 'scroll' }, parent);
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': `${T.nimi}: väärtuste jaotus seisundi kaupa, eraldi paneelid ühise skaalaga` }, sc);
    act.forEach(({ d, st }, k) => {
      const y0 = m.t + k * (ph + gap) + ph, y = (v) => y0 - ph * (v / (tk.hi || 1)), p = d.p.map((v) => v * 100);
      for (const v of tk.ticks) { h('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: 'grid' }, svg); h('text', { x: m.l - 6, y: y(v) + 4, 'text-anchor': 'end' }, svg, `${nf(0).format(v)} %`); }
      const q1 = quantile(spec, d.p, 0.25), q3 = quantile(spec, d.p, 0.75);
      if (q1 !== null && q3 !== null) h('rect', { x: x(valuePos(spec, q1)), y: y0 - ph, width: Math.max(2, x(valuePos(spec, q3)) - x(valuePos(spec, q1))), height: ph, fill: stateInk(st), opacity: 0.1 }, svg);
      if (isBars(spec)) { const bw = (W - m.l - m.r) / n, w = Math.min(26, bw - 6); p.forEach((v, i) => { if (v > 0) h('rect', { x: x(i) + bw / 2 - w / 2, y: y(v), width: w, height: y0 - y(v), rx: 2, fill: stateColor(st) }, svg); }); }
      else { h('path', { d: stepPath(p, x, y), fill: stateColor(st), 'fill-opacity': 0.75, stroke: 'none' }, svg); h('path', { d: stepLine(p, x, y), fill: 'none', stroke: stateInk(st), 'stroke-width': 1.6, 'stroke-linejoin': 'round' }, svg); }
      h('line', { x1: m.l, x2: W - m.r, y1: y0, y2: y0, class: 'axis' }, svg);
      const lab = h('g', {}, svg), sw = h('circle', { cx: m.l + 12, cy: y0 - ph + 12, r: 5, fill: stateColor(st), stroke: stateInk(st), 'stroke-width': 1.5 }, lab);
      void sw; h('text', { x: m.l + 23, y: y0 - ph + 16, class: 'strong' }, lab, D.meta.seisundid[st]);
      medianMark(svg, x, y0, spec, d, st, ph);
    });
    const yb = m.t + act.length * (ph + gap) - gap;
    xAxis(svg, spec, x, yb, W, m, T.uhik);
    hoverBins(svg, c, x, m, H);
  }
  function chartCdf(parent, c) {
    const { spec, series, W, T } = c, n = spec.n_bins, H = 300, m = { l: 52, r: 14, t: 14, b: 56 };
    const y = (v) => m.t + (H - m.t - m.b) * (1 - v), x = (i) => m.l + (W - m.l - m.r) * (i / n);
    const sc = h('div', { class: 'scroll' }, parent);
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': `${T.nimi}: kumulatiivne jaotus seisundi kaupa` }, sc);
    for (const v of [0, 0.25, 0.5, 0.75, 1]) { h('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: v === 0.5 ? 'axis' : 'grid', 'stroke-dasharray': v === 0.5 ? '4 3' : null }, svg); h('text', { x: m.l - 6, y: y(v) + 4, 'text-anchor': 'end' }, svg, `${nf(0).format(v * 100)} %`); }
    series.forEach((d, st) => {
      if (!d) return; let cum = 0; const bars = spec.kind === 'lut';
      let path = `M${x(0)},${y(0)}`;
      d.p.forEach((v, i) => { const c0 = cum; cum += v; path += bars ? ` L${x(i + 0.5)},${y(c0)} L${x(i + 0.5)},${y(cum)}` : ` L${x(i + 1)},${y(cum)}`; });
      path += ` L${x(n)},${y(Math.min(1, cum))}`;
      h('path', { d: path, fill: 'none', stroke: stateInk(st), 'stroke-width': 2.4, 'stroke-linejoin': 'round' }, svg);
      const med = exactMed(d); if (med !== null) h('circle', { cx: x(valuePos(spec, med)), cy: y(0.5), r: 5, fill: stateColor(st), stroke: stateInk(st), 'stroke-width': 2 }, svg);
    });
    xAxis(svg, spec, x, y(0), W, m, T.uhik);
    const labels = binLabels(spec);
    for (let i = 0; i < n; i++) {
      const r = h('rect', { x: x(i), y: m.t, width: x(i + 1) - x(i), height: H - m.t - m.b, fill: 'transparent' }, svg);
      tipOn(r, (t) => { tl(t, 'm', `${T.nimi} · ≤ ${labels[i].split(' … ').pop()} ${T.uhik || ''}`); series.forEach((d, st) => { if (d) { const cum = d.p.slice(0, i + 1).reduce((a, b) => a + b, 0); const row = tl(t, 'v', `${nf(0).format(cum * 100)} % pikslitest`); h('span', { class: 'm' }, row, `  ${D.meta.seisundid[st]}`); } }); });
    }
  }
  const DMODES = [['over', 'Kattuvad'], ['split', 'Eraldi paneelid'], ['cdf', 'Kumulatiivne']];
  const DMODE_HELP = {
    over: 'Kõverad ühel teljel: näed, kui palju seisundid kattuvad. Kolmnurk teljel = täpne mediaan.',
    split: 'Iga seisund oma paneelis, ühine x- ja y-skaala: näed iga jaotuse kuju. Joon = mediaan, varjutatud riba = 25–75 % pikslitest.',
    cdf: 'Kumulatiivne osakaal: „mitu % pikslitest on väärtusega ≤ x“. Mida enam kõver paremale nihkub, seda suuremad väärtused seisundis on; vahemike valik tulemust ei mõjuta. Punkt = mediaan (50 %).',
  };
  function distChart(card, li, ui) {
    const T = D.meta.teenused[li], U = D.meta.uhikud[ui];
    h('h2', {}, card, `Väärtuste jaotus seisundi kaupa · ${U.nimi}`);
    const base = distFor(li, ui, false);
    if (!base) { h('p', { class: 'sub' }, card, 'Selle teenuse ja üksuse kohta pole pikslitaseme jaotust (uuriv segumudel või puuduvad andmed).'); return; }
    const hasZero = base.zb >= 0 && base.series.some((d) => d && d.zero >= 0.03);
    const noZero = S.dzero && hasZero, dd = noZero ? distFor(li, ui, true) : base, { spec, series } = dd;
    h('p', { class: 'sub' }, card, `Iga seisundi pikslite osakaal väärtuse vahemikus; igal seisundil on oma 100 %, seega on jaotused võrreldavad sõltumata seisundi pindalast.${spec.kind === 'sqrt' ? ' Väga viltuse jaotuse tõttu on x-telg ruutjuure skaalal (vahemikud on √x-s võrdse laiusega).' : ''}${spec.kind === 'lut' ? ' Kihil on diskreetsed väärtused (skoorid või klassid).' : ''}`);
    const tools = h('div', { class: 'tools' }, card);
    h('span', { class: 'tl' }, tools, 'Vaade');
    const sg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Jaotuse vaade' }, tools);
    for (const [v, t] of DMODES) { const b = h('button', { type: 'button', 'aria-pressed': String(S.dmode === v) }, sg, t); b.onclick = () => { S.dmode = v; renderAll(true); }; }
    if (hasZero) {
      const z = Math.max(...base.series.filter(Boolean).map((d) => d.zero));
      const lb = h('label', { class: 'chk' }, tools), cb = h('input', { type: 'checkbox' }, lb); cb.checked = noZero;
      h('span', {}, lb, `Ilma täpsete nullideta (kuni ${nf(0).format(z * 100)} % pikslitest)`);
      cb.onchange = () => { S.dzero = cb.checked; renderAll(true); };
    }
    h('p', { class: 'note' }, card, DMODE_HELP[S.dmode]);
    const c = { spec, series, T, noZero, W: Math.max(320, Math.min(1240, card.clientWidth - 40 || 700)) };
    distStats(card, c);
    ({ over: chartOver, split: chartSplit, cdf: chartCdf })[S.dmode](card, c);
    const lg = stateLegend(card);
    const lm = h('li', {}, lg); h('svg', { width: 14, height: 11 }, lm).append(h('polygon', { points: '1,10 7,1 13,10', fill: cssVar('--ink-2') })); h('span', {}, lm, 'mediaan (täpne)');
    const cmp = [[0, 1], [1, 2], [0, 2]].filter(([a, b]) => series[a] && series[b]);
    if (cmp.length) {
      h('h3', {}, card, 'Jaotuste võrdlus');
      const tw = h('div', { class: 'scroll' }, card), tc = h('table', { class: 'data' }, tw), hc = h('tr', {}, h('thead', {}, tc));
      for (const t of ['Seisundipaar', 'Jaotuste kattuvus', 'Parema seisundi piksel on väärtuselt suurem', 'Mediaanide vahe']) h('th', {}, hc, t);
      const tbc = h('tbody', {}, tc);
      for (const [a, b] of cmp) {
        const pa = series[a].p, pb = series[b].p;
        let ov = 0, auc = 0, cum = 0;
        pa.forEach((v, i) => { ov += Math.min(v, pb[i]); auc += pb[i] * (cum + 0.5 * v); cum += v; });
        const ma = exactMed(series[a]), mb = exactMed(series[b]);
        const tr = h('tr', {}, tbc); h('td', {}, tr, `${D.meta.seisundid[a]} → ${D.meta.seisundid[b]}`); h('td', {}, tr, `${nf(0).format(ov * 100)} %`); h('td', {}, tr, `${nf(0).format(auc * 100)} %`); h('td', {}, tr, ma !== null && mb !== null ? `${sgn(mb - ma)} ${(T.uhik || '').split(' (')[0]}` : '–');
      }
      h('p', { class: 'note' }, card, `Kattuvus = jaotuste ühisosa (100 % = identsed, 0 % = täiesti eraldi). Teine veerg: tõenäosus, et juhuslikult valitud parema seisundi piksli väärtus on suurem kui halvema seisundi pikslil (50 % = vahet pole; võrdsed vahemikud loetakse pooleks).${noZero ? ' Praegune vaade on ilma täpsete nullideta.' : ''} Kattuvus ja tõenäosus on arvutatud pikslitaseme jaotustest vahemike täpsusega, mediaanid on täpsed; pikslid on ruumiliselt sõltuvad, seega on need kirjeldavad näitajad, mitte olulisuse testid (olulisus on eespool, 10 km klastrite bootstrapiga).`);
    }
    const det = h('details', {}, card); h('summary', {}, det, 'Tabelivaade (osakaal %)');
    const sc2 = h('div', { class: 'scroll' }, det), t2 = h('table', { class: 'data' }, sc2), hr = h('tr', {}, h('thead', {}, t2)), labels = binLabels(spec);
    for (const t of [`Vahemik (${T.uhik || 'väärtus'})`, ...D.meta.seisundid]) h('th', {}, hr, t);
    const tb = h('tbody', {}, t2);
    labels.forEach((l, i) => { const tr = h('tr', {}, tb); h('td', {}, tr, l); series.forEach((d) => h('td', {}, tr, d ? nf(1).format(d.p[i] * 100) : '–')); });
  }
  function distMini(parent, li, ui) {
    const dd = distFor(li, ui, false); if (!dd) return null;
    const { spec, series } = dd, n = spec.n_bins, W = 226, H = 84, m = { l: 4, r: 4, t: 6, b: 14 };
    const top = Math.max(...series.filter(Boolean).flatMap((d) => d.p)) || 1;
    const x = (i) => m.l + (W - m.l - m.r) * (i / n), y = (v) => m.t + (H - m.t - m.b) * (1 - v / top);
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': `${D.meta.teenused[li].nimi}: jaotus seisundi kaupa` }, parent);
    series.forEach((d, st) => {
      if (!d) return;
      if (isBars(spec)) { const bw = (W - m.l - m.r) / n, w = Math.max(2, Math.min(9, (bw - 2) / 3)); d.p.forEach((v, i) => { if (v > 0) h('rect', { x: x(i) + bw / 2 + (st - 1) * (w + 1) - w / 2, y: y(v), width: w, height: y(0) - y(v), fill: stateColor(st) }, svg); }); }
      else { h('path', { d: stepPath(d.p, x, y), fill: stateColor(st), 'fill-opacity': 0.28, stroke: 'none' }, svg); h('path', { d: stepLine(d.p, x, y), fill: 'none', stroke: stateInk(st), 'stroke-width': 1.6, 'stroke-linejoin': 'round' }, svg); }
    });
    h('line', { x1: m.l, x2: W - m.r, y1: y(0), y2: y(0), class: 'axis' }, svg);
    series.forEach((d, st) => { if (d) medianMark(svg, x, y(0), spec, d, st, 0); });
    return { spec, series };
  }
  function distTab(root) {
    const M = D.meta, card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Väärtuste jaotus seisundi kaupa: kõik teenused');
    h('p', { class: 'sub' }, card, 'Iga kaart näitab teenuse pikslite jaotust kolmes seisundis (igal seisundil oma 100 %; y-telg on kaardi sees normeeritud, et kuju oleks võrreldav). Kolmnurgad teljel = täpsed mediaanid. Kui kõverad on üksteisest eraldi, muutub teenus seisundi vahel; kui kattuvad, ei muutu. Klõpsa kaarti, et avada täpne jaotus, tabel ja hinnangud.');
    const ctl = h('div', { class: 'frow' }, card); const g = h('div', { class: 'fgrp wide' }, ctl); h('label', { for: 'du2' }, g, 'Ökosüsteem / alamökosüsteem');
    const sel = h('select', { id: 'du2' }, g);
    const us = M.uhikud.map((u, i) => ({ u, i })).filter(({ u }) => S.ecos.has(u.eco));
    if (!us.some(({ i }) => i === S.profUnit) && us.length) S.profUnit = us[0].i;
    for (const { u, i } of us) { const o = h('option', { value: i }, sel, `${u.tase === 'okosusteem' ? '▪ ' : '   '}${u.nimi}`); if (i === S.profUnit) o.selected = true; }
    sel.onchange = () => { S.profUnit = +sel.value; renderAll(true); };
    stateLegend(card);
    const minis = h('div', { class: 'minis big' }, card); let n = 0;
    for (const { t, i } of visLayers()) {
      if (!distFor(i, S.profUnit, false)) continue;
      const m = h('div', { class: 'mini', tabindex: 0, role: 'button', 'aria-label': `Ava detail: ${t.nimi}` }, minis);
      h('h4', {}, m, t.nimi); h('div', { class: 'u' }, m, `${t.grupp}${t.uhik ? ` · ${t.uhik}` : ''}`);
      const dm = distMini(m, i, S.profUnit), U = (t.uhik || '').split(' (')[0];
      const meds = dm.series.map((d) => exactMed(d));
      h('div', { class: 'nm2' }, m, `mediaan: ${meds.map((v) => (v === null ? '–' : fmt(v))).join(' → ')} ${U}`);
      const foot = h('div', { class: 'foot' }, m), r2 = D.byPair.get(`${i}|${S.profUnit}|2`), e = est(r2);
      h('span', { class: `pill${e && e.ok && e.sig ? ' sig' : ''}` }, foot, e && e.ok ? `vilets → hea: ${pct(e.rel)}${e.sig ? ' · oluline' : ' · ei ole oluline'}` : 'vilets → hea: ebapiisavalt andmeid');
      const z = Math.max(...dm.series.filter(Boolean).map((d) => d.zero)); if (z >= 0.05) h('span', { class: 'pill zero' }, foot, `täpselt 0: ${nf(0).format(z * 100)} %`);
      const go = () => { S.detail.layer = i; S.detail.unit = S.profUnit; S.tab = 'teenus'; renderAll(true); scrollTo(0, 0); };
      m.onclick = go; m.onkeydown = (ev) => { if (ev.key === 'Enter') go(); };
      n++;
    }
    if (!n) h('p', { class: 'empty' }, card, D.distSpec && Object.keys(D.distSpec).length ? 'Selles üksuses pole valitud teenustel jaotust.' : 'Jaotuse andmed puuduvad.');
  }

  /* ---------- Kihtide ülevaade (ühe pilguga kõigi kihtide jaotused) ---------- */
  function pooled(li, units, noZero) {
    const spec = D.distSpec[li]; if (!spec) return null;
    const nb = spec.n_bins, zb = binOf(spec, 0), st = [0, 1, 2].map(() => new Array(nb).fill(0)), zs = [0, 0, 0];
    let N = 0;
    for (const u of units) for (let s = 0; s < 3; s++) {
      const d = D.dist.get(`${li}|${u}|${s}`), c = D.byCell.get(`${li}|${u}|${s}`); if (!d || !c) continue;
      N += c.n; zs[s] += c.n * d.zero / 10000;
      d.shares.forEach((v, i) => { st[s][i] += c.n * v / 10000; });
    }
    if (!N) return null;
    const Z = zs.reduce((a, b) => a + b, 0);
    let use = N;
    if (noZero && zb >= 0 && Z > 0) { for (let s = 0; s < 3; s++) st[s][zb] = Math.max(0, st[s][zb] - zs[s]); use = N - Z; }
    if (!(use > 0)) return null;
    const stack = st.map((a) => a.map((v) => v / use)), total = new Array(nb).fill(0).map((_, i) => stack[0][i] + stack[1][i] + stack[2][i]);
    return { spec, stack, total, zero: Z / N, nPix: N };
  }
  let twinCache = null;
  /** Kihid, mille seisundikaupa jaotuse kuju on kõigis ökosüsteemides sama (kattuvus ≥ 0,97), st erinevad ainult skaala poolest. */
  function twins() {
    if (twinCache) return twinCache;
    twinCache = new Map();
    const ls = Object.keys(D.distSpec).map(Number).sort((a, b) => a - b), ecoU = D.meta.uhikud.map((u, i) => ({ u, i })).filter(({ u }) => u.tase === 'okosusteem').map(({ i }) => i);
    for (let a = 0; a < ls.length; a++) for (let b = a + 1; b < ls.length; b++) {
      const A = D.distSpec[ls[a]], B = D.distSpec[ls[b]];
      if (A.kind !== B.kind || A.n_bins !== B.n_bins) continue;
      let worst = 1, cnt = 0;
      for (const u of ecoU) for (let s = 0; s < 3; s++) {
        const x = D.dist.get(`${ls[a]}|${u}|${s}`), y = D.dist.get(`${ls[b]}|${u}|${s}`); if (!x || !y) continue;
        cnt++; worst = Math.min(worst, x.shares.reduce((t, v, i) => t + Math.min(v, y.shares[i]), 0) / 10000);
      }
      if (cnt >= 6 && worst >= 0.97) { twinCache.set(ls[a], ls[b]); twinCache.set(ls[b], ls[a]); }
    }
    return twinCache;
  }
  function layerTile(parent, t, i, units, opts) {
    const P = pooled(i, units, opts.noZero); if (!P) return false;
    const { spec } = P, n = spec.n_bins, W = 236, H = 96, m = { l: 4, r: 4, t: 14, b: 22 };
    const top = Math.max(...P.total) || 1, x = (k) => m.l + (W - m.l - m.r) * (k / n), y = (v) => m.t + (H - m.t - m.b) * (1 - v / top);
    const tile = h('div', { class: 'mini', tabindex: 0, role: 'button', 'aria-label': `Ava detail: ${t.nimi}` }, parent);
    h('h4', {}, tile, t.nimi); h('div', { class: 'u' }, tile, `${t.grupp}${t.uhik ? ` · ${t.uhik}` : ''}`);
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': `${t.nimi}: väärtuste jaotus${opts.stack ? ' seisundi koosseisuga' : ''}` }, tile);
    const bw = (W - m.l - m.r) / n;
    for (let k = 0; k < n; k++) {
      if (opts.stack) {
        let base = 0;
        for (let s = 0; s < 3; s++) { const v = P.stack[s][k]; if (v <= 0) continue; const y1 = y(base + v), y0 = y(base); h('rect', { x: x(k) + (n > 14 ? 0.2 : 1), y: y1, width: Math.max(1, bw - (n > 14 ? 0.4 : 2)), height: Math.max(0.5, y0 - y1), fill: stateColor(s) }, svg); base += v; }
      } else if (P.total[k] > 0) h('rect', { x: x(k) + (n > 14 ? 0.2 : 1), y: y(P.total[k]), width: Math.max(1, bw - (n > 14 ? 0.4 : 2)), height: y(0) - y(P.total[k]), fill: cssVar('--neutral') }, svg);
    }
    h('line', { x1: m.l, x2: W - m.r, y1: y(0), y2: y(0), class: 'axis' }, svg);
    const tks = xTicks(spec, 4); tks.forEach((tk, j) => h('text', { x: Math.max(14, Math.min(W - 14, x(tk.pos))), y: H - 6, 'text-anchor': 'middle', style: 'font-size:10.5px' }, svg, tk.label));
    h('text', { x: W - m.r, y: 10, 'text-anchor': 'end', style: 'font-size:10.5px' }, svg, `kõrgeim tulp ${nf(top >= 0.1 ? 0 : 1).format(top * 100)} %`);
    const med = quantile(spec, P.total, 0.5), foot = h('div', { class: 'foot' }, tile);
    h('span', { class: 'pill' }, foot, `mediaan ≈ ${med === null ? '–' : fmt(med)}`);
    if (P.zero >= 0.03) h('span', { class: 'pill zero' }, foot, `täpselt 0: ${nf(0).format(P.zero * 100)} %`);
    const tw = twins().get(i); if (tw !== undefined) h('span', { class: 'pill' }, foot, `sama kuju kui «${D.meta.teenused[tw].nimi.slice(0, 34)}${D.meta.teenused[tw].nimi.length > 34 ? '…' : ''}»`);
    const go = () => { S.detail.layer = i; const u0 = units.find((u) => D.byCell.has(`${i}|${u}|0`) || D.byCell.has(`${i}|${u}|1`)); S.detail.unit = u0 === undefined ? S.detail.unit : u0; S.tab = 'teenus'; renderAll(true); scrollTo(0, 0); };
    tile.onclick = go; tile.onkeydown = (ev) => { if (ev.key === 'Enter') go(); };
    tipOn(tile, (tp) => { tl(tp, 'm', t.nimi); tl(tp, 'v', `mediaan ≈ ${med === null ? '–' : fmt(med)} ${(t.uhik || '').split(' (')[0]}`); tl(tp, 'm', 'ligikaudne: mitme seisundi koondjaotuse vahemike järgi'); tl(tp, 'm', `${nf(1).format(P.nPix * (t.res || 10) ** 2 / 1e6)} km² seisundiga pindala`); });
    P.med = med; return P;
  }
  function layersTab(root) {
    const M = D.meta, card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Kihtide ülevaade: kõigi teenuste väärtuste jaotus');
    h('p', { class: 'sub' }, card, 'Üks pilk kõigile kihtidele: kuidas jagunevad teenuse väärtused pikslite vahel. Osakaal (%), mitte pikslite arv, nii on kihid võrreldavad ka eri eraldusvõime korral. Arvesse lähevad ainult seisundiga pikslid (vilets, keskmine, hea). Tulba värvid näitavad, millisest seisundist väärtus pärineb.');
    const ctl = h('div', { class: 'frow' }, card);
    const g = h('div', { class: 'fgrp wide' }, ctl); h('label', { for: 'lu' }, g, 'Üksus');
    const sel = h('select', { id: 'lu' }, g);
    const o0 = h('option', { value: -1 }, sel, '▪ Kõik ökosüsteemid kokku'); if (S.lunit === -1) o0.selected = true;
    for (const [i, u] of M.uhikud.entries()) { if (!S.ecos.has(u.eco)) continue; const o = h('option', { value: i }, sel, `${u.tase === 'okosusteem' ? '▪ ' : '   '}${u.nimi}`); if (S.lunit === i) o.selected = true; }
    sel.onchange = () => { S.lunit = +sel.value; renderAll(true); };
    const g2 = h('div', { class: 'fgrp' }, ctl); h('label', { for: 'ls' }, g2, 'Järjesta');
    const ss = h('select', { id: 'ls' }, g2);
    for (const [v, t] of [['grupp', 'Teenusegrupi ja nime järgi'], ['zero', 'Täpsete nullide osakaalu järgi'], ['skew', 'Mediaan / ülemine ots (viltuse järgi)']]) { const o = h('option', { value: v }, ss, t); if (S.lsort === v) o.selected = true; }
    ss.onchange = () => { S.lsort = ss.value; renderAll(true); };
    const tools = h('div', { class: 'tools' }, card);
    h('span', { class: 'tl' }, tools, 'Värv');
    const sg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Tulpade värv' }, tools);
    for (const [v, t] of [[true, 'Seisundi koosseis'], [false, 'Kõik pikslid kokku']]) { const b = h('button', { type: 'button', 'aria-pressed': String(S.lstack === v) }, sg, t); b.onclick = () => { S.lstack = v; renderAll(true); }; }
    const lb = h('label', { class: 'chk' }, tools), cb = h('input', { type: 'checkbox' }, lb); cb.checked = S.lzero; h('span', {}, lb, 'Ilma täpsete nullideta'); cb.onchange = () => { S.lzero = cb.checked; renderAll(true); };
    if (S.lstack) stateLegend(card);
    const units = S.lunit === -1 ? M.uhikud.map((u, i) => ({ u, i })).filter(({ u }) => u.tase === 'okosusteem' && S.ecos.has(u.eco)).map(({ i }) => i) : [S.lunit];
    const rows = visLayers().map(({ t, i }) => ({ t, i, P: pooled(i, units, S.lzero) })).filter((r) => r.P);
    const skew = (r) => { const med = quantile(r.P.spec, r.P.total, 0.5), hi = quantile(r.P.spec, r.P.total, 0.95); return med !== null && hi ? med / hi : 1; };
    if (S.lsort === 'zero') rows.sort((a, b) => b.P.zero - a.P.zero); else if (S.lsort === 'skew') rows.sort((a, b) => skew(a) - skew(b));
    const wrap = h('div', {}, card); let last = null, grid = null;
    for (const r of rows) {
      if (S.lsort === 'grupp') { if (r.t.grupp !== last) { h('h3', {}, wrap, r.t.grupp); grid = h('div', { class: 'minis big' }, wrap); last = r.t.grupp; } }
      else if (!grid) grid = h('div', { class: 'minis big' }, wrap);
      layerTile(grid, r.t, r.i, units, { stack: S.lstack, noZero: S.lzero });
    }
    if (!rows.length) h('p', { class: 'empty' }, card, 'Valitud filtritele ei vasta ühtegi jaotust.');
    const missing = visLayers().filter(({ i }) => !D.distSpec[i]).map(({ t }) => t.nimi);
    if (missing.length) h('p', { class: 'note' }, card, `Pikslitaseme jaotust ei ole (uuriv segumudel / jäme ruudustik): ${missing.join('; ')}.`);
    h('p', { class: 'note' }, card, 'Iga kaardi y-telg on kaardi sees normeeritud (kõrgeim tulp = ülaserv; väärtus nurgas), kuna eesmärk on jaotuse kuju. Ruutjuure skaalal kihtidel (viltused jaotused) on x-telje sildid mittelineaarselt paigas. „Sama kuju“ tähendab, et seisundikaupa jaotuste kattuvus on kõigis ökosüsteemides ≥ 97 % (kihid erinevad skaala poolest, nt kg vs EUR).');
    const det = h('details', { class: 'fwrap' }, card); h('summary', {}, det, 'Mida õppisime kolleegi graafikust ja kuidas seda siin parandati');
    const sc = h('div', { class: 'scroll' }, det), t = h('table', { class: 'ideas-t' }, sc), hd = h('tr', {}, h('thead', {}, t));
    for (const c of ['Kolleegi graafikul', 'Miks see segab', 'Siin']) h('th', {}, hd, c);
    const tb = h('tbody', {}, t);
    for (const r of [
      ['Y-telg on pikslite arv (1e7, 1e8)', 'paneele ei saa omavahel võrrelda; 930 m ja 5–10 m kihtidel on arvud erineva suurusjärguga', 'osakaal (%) ja „kõrgeim tulp“ märge'],
      ['Pealkiri on failinimi', 'ekspert peab nime meelde tuletama; pikad nimed jooksevad kokku', 'teenuse nimi + grupp + ühik; rühmitamine'],
      ['Kõik pikslid ühes tulbas', 'ei näita, kas jaotus sõltub seisundist (projekti põhiküsimus)', 'virnastatud tulbad seisundi värvides'],
      ['Täpne null domineerib', 'ülejäänud jaotus on nähtamatu', 'nullide osakaal sildina; lüliti „ilma täpsete nullideta“; järjestus nullide järgi'],
      ['Telje sildid nagu 26.88 või 79.1845; sama joonis diskreetsetele ja pidevatele kihtidele', 'sildid on müra; skoorid vajavad tulpi, pidevad kihid histogrammi', 'ümmargused teljesildid; diskreetsed kihid tulpadena'],
      ['Viltused jaotused lineaarsel teljel', 'tipp surutakse vasakule, saba on tühi', 'ruutjuure telg viltustel kihtidel (märgitud)'],
      ['Mõned paneelid näevad identsed', 'dubleerivad infot', 'kontrollitud kattuvusega; märge „sama kuju kui …“'],
    ]) { const tr = h('tr', {}, tb); for (const c of r) h('td', {}, tr, c); }
  }

  function levelsChart(card, li, ui) {
    const T = D.meta.teenused[li], nz = S.lvnz, z = nz ? '_nz' : '';
    h('h2', {}, card, 'Teenuse tase seisundi kaupa');
    const tools = h('div', { class: 'tools' }, card), sg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Milliseid piksleid näidata' }, tools);
    for (const [v, t] of [[false, 'Kõik pikslid'], [true, 'Ainult pikslid, kus teenus esineb (väärtus > 0)']]) { const bt = h('button', { type: 'button', 'aria-pressed': String(S.lvnz === v) }, sg, t); bt.onclick = () => { S.lvnz = v; renderAll(true); }; }
    h('p', { class: 'sub' }, card, `Punkt = täpne pikslimediaan${nz ? ' kohtades, kus teenus esineb' : ''}; kast = 1 km plokkide mediaanide vahemik Q1–Q3, vurr = 5.–95. protsentiil, vahetõmmis = plokkide mediaanide mediaan. „Esineb“ = mitu % pindalast on väärtusega üle 0.`);
    const cells = [0, 1, 2].map((s2) => D.byCell.get(`${li}|${ui}|${s2}`));
    if (!cells.some(Boolean)) { h('p', { class: 'empty' }, card, 'Andmeid pole.'); return; }
    const W = Math.max(320, Math.min(560, card.clientWidth - 30 || 520)), H = 290, m = { l: 62, r: 12, t: 26, b: 40 };
    const vals = cells.filter(Boolean).flatMap((c) => [c[`mq05${z}`], c[`mq95${z}`], c[`median${z}`]].filter(has));
    if (!vals.length) { h('p', { class: 'empty' }, card, 'Selles vaates andmeid pole.'); return; }
    let lo = Math.min(...vals), hi = Math.max(...vals); if (lo > 0 && lo < 0.35 * hi) lo = 0;
    const pad = (hi - lo) * 0.06 || 1; const tk = niceTicks(lo - (lo === 0 ? 0 : pad), hi + pad, 5);
    const y = yScale(tk.lo, tk.hi, H, m);
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': `${T.nimi}: tase seisundi kaupa` }, card);
    for (const v of tk.ticks) { h('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: 'grid' }, svg); h('text', { x: m.l - 6, y: y(v) + 4, 'text-anchor': 'end' }, svg, fmt(v)); }
    h('text', { x: 4, y: 12 }, svg, T.uhik || '');
    const bw = (W - m.l - m.r) / 3;
    cells.forEach((c, st) => {
      const cx = m.l + bw * st + bw / 2, w = Math.min(44, bw * 0.45);
      h('text', { x: cx, y: H - 22, 'text-anchor': 'middle', class: 'lbl' }, svg, D.meta.seisundid[st]);
      if (!c || !has(c[`median${z}`])) { h('text', { x: cx, y: H - 8, 'text-anchor': 'middle' }, svg, 'andmeid pole'); return; }
      const med = c[`median${z}`], occ = c.n ? (c.n_nz || 0) / c.n : null;
      const g = h('g', { tabindex: 0, role: 'img', 'aria-label': `${D.meta.seisundid[st]}: mediaan ${fmt(med)}` }, svg);
      if (has(c[`mq05${z}`]) && has(c[`mq95${z}`])) {
        h('line', { x1: cx, x2: cx, y1: y(c[`mq05${z}`]), y2: y(c[`mq95${z}`]), stroke: cssVar('--ink-2'), 'stroke-width': 1.5 }, g);
        h('rect', { x: cx - w / 2, y: y(c[`mq75${z}`]), width: w, height: Math.max(2, y(c[`mq25${z}`]) - y(c[`mq75${z}`])), rx: 3, fill: stateColor(st) }, g);
        h('line', { x1: cx - w / 2, x2: cx + w / 2, y1: y(c[`mq50${z}`]), y2: y(c[`mq50${z}`]), stroke: cssVar('--surface'), 'stroke-width': 2 }, g);
      }
      h('circle', { cx, cy: y(med), r: 5, fill: cssVar('--ink'), stroke: cssVar('--surface'), 'stroke-width': 2 }, g);
      h('text', { x: cx + w / 2 + 8, y: y(med) + 4, class: 'strong' }, svg, fmt(med));
      h('text', { x: cx, y: H - 8, 'text-anchor': 'middle' }, svg, occ === null ? '' : `esineb ${nf(0).format(occ * 100)} %`);
      tipOn(g, (t) => {
        tl(t, 'm', `${T.nimi} · ${D.meta.seisundid[st]}`); tl(t, 'v', `mediaan ${fmt(c.median)} ${T.uhik || ''}`);
        tl(t, 'm', `kohtades, kus teenus esineb: mediaan ${fmt(c.median_nz)} · keskmine (kõik pikslid) ${fmt(c.mean)}`);
        if (occ !== null) tl(t, 'm', `teenus esineb ${nf(0).format(occ * 100)} % pindalast · ${nf(0).format(c.n * (D.meta.teenused[li].res || 10) ** 2 / 1e6)} km²`);
        tl(t, 'm', `plokkide mediaanide Q1–Q3: ${fmt(c[`mq25${z}`])} … ${fmt(c[`mq75${z}`])} (${nf(0).format(c[`blocks_med${z}`] || 0)} plokki)`);
      });
    });
    if (!nz && cells.some((c) => c && c.mq50 === 0)) h('p', { class: 'note' }, card, 'Vähemalt ühes seisundis on üle poole plokkidest mediaaniga 0, seega kast on nulli juures. Vali „Ainult pikslid, kus teenus esineb“, et näha väärtust seal, kus teenust on.');
  }

  function deltaChart(card, li, ui, mode) {
    const T = D.meta.teenused[li];
    h('h2', {}, card, mode === 'rel' ? 'Muutus seisundipaaride vahel (suhteline)' : `Muutus seisundipaaride vahel (${(T.uhik || 'absoluutne').split(' (')[0]})`);
    h('p', { class: 'sub' }, card, 'Mediaanide muutus. Punkt = hinnang, joon = 95 % usaldusvahemik (10 km klastrite bootstrap). Täis punkt = paaritatud, tühi ring = paaritamata. Sinine = oluline (FDR q < 0,05), hall = ei ole oluline.');
    const rows = [];
    for (let p = 0; p < 3; p++) { const r = D.byPair.get(`${li}|${ui}|${p}`); if (!r) continue; for (const k of ['m', 'u']) rows.push({ p, k, r, e: estOf(r, k) }); }
    const val = (e) => (mode === 'rel' ? { v: has(e.rel) ? e.rel : null, lo: has(e.lo) && has(e.rel) && e.d ? e.rel * (e.lo / e.d) : null, hi: has(e.hi) && has(e.rel) && e.d ? e.rel * (e.hi / e.d) : null } : { v: e.d, lo: has(e.lo) ? e.lo : null, hi: has(e.hi) ? e.hi : null });
    const pts = rows.filter((x) => x.e.ok && val(x.e).v !== null);
    if (!pts.length) { h('p', { class: 'empty' }, card, 'Selle ühiku kohta pole piisavalt andmeid hinnangu jaoks.'); return; }
    const W = Math.max(320, Math.min(560, card.clientWidth - 30 || 520)), rowH = 30, m = { l: 214, r: 16, t: 10, b: 30 }, H = m.t + m.b + rows.length * rowH;
    const all = pts.flatMap((x) => { const v = val(x.e); return [v.v, v.lo, v.hi, 0].filter((z) => z !== null && z !== undefined); });
    const tk = niceTicks(Math.min(...all), Math.max(...all), 5);
    const x = (v) => m.l + (W - m.l - m.r) * ((v - tk.lo) / (tk.hi - tk.lo || 1));
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': 'Hinnangud ja usaldusvahemikud' }, card);
    for (const v of tk.ticks) { h('line', { x1: x(v), x2: x(v), y1: m.t, y2: H - m.b, class: 'grid' }, svg); h('text', { x: x(v), y: H - 12, 'text-anchor': 'middle' }, svg, mode === 'rel' ? `${nf(0).format(v * 100)} %` : fmt(v)); }
    h('line', { x1: x(0), x2: x(0), y1: m.t, y2: H - m.b, class: 'zero' }, svg);
    rows.forEach((row, i) => {
      const cy = m.t + rowH * i + rowH / 2, v = val(row.e);
      h('text', { x: 4, y: cy + 4, class: 'lbl' }, svg, `${D.meta.paarid[row.p].replace('→', ' → ')} · ${row.k === 'm' ? 'paaritatud' : 'paaritamata'}`);
      const g = h('g', { tabindex: 0, role: 'img', 'aria-label': `${D.meta.paarid[row.p]} ${row.k}: ${row.e.ok ? pct(row.e.rel, 1) : 'pole hinnatav'}` }, svg);
      if (!row.e.ok || v.v === null) { h('text', { x: m.l + 6, y: cy + 4 }, g, 'ebapiisavalt andmeid'); }
      else {
        const col = row.e.sig ? cssVar('--accent') : cssVar('--muted');
        if (v.lo !== null && v.hi !== null) h('line', { x1: x(v.lo), x2: x(v.hi), y1: cy, y2: cy, stroke: col, 'stroke-width': 2, 'stroke-linecap': 'round' }, g);
        h('circle', { cx: x(v.v), cy, r: 5, fill: row.k === 'm' ? col : cssVar('--surface'), stroke: col, 'stroke-width': row.k === 'm' ? 2 : 2.5 }, g);
      }
      h('rect', { x: m.l - 4, y: cy - rowH / 2, width: W - m.l, height: rowH, fill: 'transparent' }, g);
      tipOn(g, (t) => pairTip(t, row.r));
    });
    const lg = h('ul', { class: 'legend' }, card);
    const a = h('li', {}, lg); h('span', { class: 'sw dot', style: `--c:${cssVar('--accent')}` }, a); h('span', {}, a, 'oluline');
    const b2 = h('li', {}, lg); h('span', { class: 'sw dot', style: `--c:${cssVar('--muted')}` }, b2); h('span', {}, b2, 'ei ole oluline');
  }

  const LETTER_ORDER = ['A', 'A1', 'A2', 'A-B', 'A-C', 'B', 'B1', 'B2', 'C', 'C1', 'C2', 'D', 'D1', 'D2', 'E', 'F'];
  function classChart(card, li, ui) {
    const T = D.meta.teenused[li], U = D.meta.uhikud[ui];
    h('h2', {}, card, 'Algsel seisundiskaalal');
    h('p', { class: 'sub' }, card, `Täpne mediaan iga algse seisundiklassi (${U.tase === 'alam' ? 'alamökosüsteemi' : 'ökosüsteemi kõigi alamökosüsteemide'}) kohta; värv = ühtlustatud seisund. Näitab, kas muutus on astmeline või ühtlane.`);
    const items = (D.alg.get(`${li}|${ui}`) || []).map((r) => ({ ...r, v: r.median })).filter((r) => has(r.v)).sort((a, b) => LETTER_ORDER.indexOf(a.k) - LETTER_ORDER.indexOf(b.k));
    if (!items.length) { h('p', { class: 'empty' }, card, 'Andmeid pole.'); return; }
    const W = Math.max(320, Math.min(560, card.clientWidth - 30 || 520)), H = 270, m = { l: 62, r: 10, t: 26, b: 44 };
    const hi = Math.max(...items.map((i) => i.v), 0), lo = Math.min(...items.map((i) => i.v), 0);
    const tk = niceTicks(lo, hi * 1.05 || 1, 5), y = yScale(tk.lo, tk.hi, H, m);
    const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': 'Mediaan algse seisundiklassi kaupa' }, card);
    for (const v of tk.ticks) { h('line', { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: 'grid' }, svg); h('text', { x: m.l - 6, y: y(v) + 4, 'text-anchor': 'end' }, svg, fmt(v)); }
    h('text', { x: 4, y: 12 }, svg, T.uhik || '');
    const bw = (W - m.l - m.r) / items.length, w = Math.min(24, bw * 0.7);
    items.forEach((it, i) => {
      const cx = m.l + bw * i + bw / 2, y0 = y(0), y1 = y(it.v);
      const g = h('g', { tabindex: 0, role: 'img', 'aria-label': `${it.k}: ${fmt(it.v)}` }, svg);
      const top = Math.min(y0, y1), ht = Math.max(1, Math.abs(y1 - y0));
      h('path', { d: `M${cx - w / 2},${y0} V${top + 4} q0,-4 4,-4 h${w - 8} q4,0 4,4 V${y0} z`, fill: stateColor(it.st >= 0 ? it.st : 0), transform: it.v < 0 ? `rotate(180 ${cx} ${y0})` : null }, g);
      h('rect', { x: cx - w / 2 - 2, y: top - 4, width: w + 4, height: ht + 8, fill: 'transparent' }, g);
      h('text', { x: cx, y: H - 28, 'text-anchor': 'middle', class: 'lbl' }, svg, it.k);
      if (bw >= 38) h('text', { x: cx, y: (it.v >= 0 ? top : top + ht) + (it.v >= 0 ? -5 : 13), 'text-anchor': 'middle' }, svg, fmt(it.v));
      tipOn(g, (t) => { tl(t, 'm', `${T.nimi} · klass ${it.k} (${D.meta.seisundid[it.st] || ''})`); tl(t, 'v', `mediaan ${fmt(it.v)} ${T.uhik || ''}`); tl(t, 'm', `kohtades, kus teenus esineb: ${fmt(it.mnz)} · keskmine ${fmt(it.mean)}`); tl(t, 'm', `${nf(0).format(it.n)} pikslit`); });
    });
    h('text', { x: m.l, y: H - 8 }, svg, 'algne seisundiklass (A = parim)');
    const lg = h('ul', { class: 'legend' }, card);
    D.meta.seisundid.forEach((s2, i) => { const li2 = h('li', {}, lg); swatch(li2, i); h('span', {}, li2, s2); });
  }

  function pairTable(card, li, ui) {
    h('h2', {}, card, 'Tabelivaade');
    const sc = h('div', { class: 'scroll' }, card);
    const t = h('table', { class: 'data' }, sc);
    const hd = h('tr', {}, h('thead', {}, t));
    for (const c of ['Seisundipaar', 'Hinnang (mediaanid)', 'Δ', 'Δ %', '95 % CI (Δ)', 'p', 'q (FDR)', 'Oluline', 'Paare/plokke']) h('th', {}, hd, c);
    const tb = h('tbody', {}, t);
    for (let p = 0; p < 3; p++) {
      const r = D.byPair.get(`${li}|${ui}|${p}`); if (!r) continue;
      for (const k of ['m', 'u']) {
        const e = estOf(r, k), tr = h('tr', {}, tb);
        h('td', {}, tr, D.meta.paarid[p].replace('→', ' → ')); h('td', {}, tr, k === 'm' ? 'paaritatud' : 'paaritamata');
        h('td', {}, tr, e.ok ? sgn(e.d) : '–'); h('td', {}, tr, e.ok ? pct(e.rel, 1) : '–'); h('td', {}, tr, e.ok ? `${sgn(e.lo)} … ${sgn(e.hi)}` : '–');
        h('td', {}, tr, e.ok ? pfmt(e.p) : '–'); h('td', {}, tr, e.ok ? pfmt(e.q) : '–'); h('td', { class: e.ok && e.sig ? 'sig-y' : 'sig-n' }, tr, e.ok ? (e.sig ? 'jah' : 'ei') : 'ebapiisav');
        h('td', {}, tr, k === 'm' ? `${nf(0).format(r.n_strata || 0)} paari` : `${nf(0).format(r.blocks_a)} / ${nf(0).format(r.blocks_b)} plokki`);
      }
    }
  }

  /* ---------- Profiil: kõik teenused ühe üksuse sees ---------- */
  function profile(root) {
    const M = D.meta, card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Kõik teenused ühe ökosüsteemi sees');
    h('p', { class: 'sub' }, card, 'Iga mini-graafik näitab teenuse mediaani kolmes seisundis kihi enda ühikus (igal graafikul oma skaala). Joon on ainult lugemise abi; hinnangud ja olulisus on teenuse detailis. Klõpsa graafikut, et avada detail.');
    const ctl = h('div', { class: 'frow' }, card); const g = h('div', { class: 'fgrp wide' }, ctl); h('label', { for: 'pu' }, g, 'Ökosüsteem / alamökosüsteem');
    const sel = h('select', { id: 'pu' }, g);
    const us = M.uhikud.map((u, i) => ({ u, i })).filter(({ u }) => S.ecos.has(u.eco));
    if (!us.some(({ i }) => i === S.profUnit) && us.length) S.profUnit = us[0].i;
    for (const { u, i } of us) { const o = h('option', { value: i }, sel, `${u.tase === 'okosusteem' ? '▪ ' : '   '}${u.nimi}`); if (i === S.profUnit) o.selected = true; }
    sel.onchange = () => { S.profUnit = +sel.value; renderAll(true); };
    const minis = h('div', { class: 'minis' }, card); let n = 0, lastG = null;
    for (const { t, i } of visLayers()) {
      const cs = [0, 1, 2].map((s) => D.byCell.get(`${i}|${S.profUnit}|${s}`));
      if (!cs.every((c) => c && has(c.median))) continue;
      n++;
      const idx = cs.map((c) => c.median), r2 = D.byPair.get(`${i}|${S.profUnit}|2`), e = est(r2);
      const m = h('div', { class: 'mini', tabindex: 0, role: 'button', 'aria-label': `Ava detail: ${t.nimi}` }, minis);
      h('h4', {}, m, t.nimi); h('div', { class: 'u' }, m, `${t.grupp}${t.uhik ? ` · ${t.uhik}` : ''}`);
      const W = 190, H = 70, mm = { l: 6, r: 6, t: 8, b: 8 };
      const lo = Math.min(...idx, 0), hi = Math.max(...idx, 0), sp = hi - lo || 1, y = yScale(lo - sp * 0.1, hi + sp * 0.1, H, mm), x = (s) => mm.l + (W - mm.l - mm.r) * (s / 2);
      const svg = h('svg', { width: W, height: H, role: 'img', 'aria-label': `${t.nimi}: mediaan ${idx.map((v) => fmt(v)).join(', ')}` }, m);
      h('line', { x1: mm.l, x2: W - mm.r, y1: y(0), y2: y(0), class: 'grid' }, svg);
      h('polyline', { points: idx.map((v, s) => `${x(s)},${y(v)}`).join(' '), fill: 'none', stroke: cssVar('--ink-2'), 'stroke-width': 2, 'stroke-linejoin': 'round' }, svg);
      idx.forEach((v, s) => h('circle', { cx: x(s), cy: y(v), r: 5, fill: stateColor(s), stroke: cssVar('--surface'), 'stroke-width': 2 }, svg));
      h('div', { class: 'u' }, m, e && e.ok ? `vilets → hea: ${has(e.rel) ? pct(e.rel) : sgn(e.d)}${e.sig ? '' : ' (ei ole oluline)'}` : 'vilets → hea: ebapiisavalt andmeid');
      const go = () => { S.detail.layer = i; S.detail.unit = S.profUnit; S.tab = 'teenus'; renderAll(true); scrollTo(0, 0); };
      m.onclick = go; m.onkeydown = (ev) => { if (ev.key === 'Enter') go(); };
      tipOn(m, (tp) => { tl(tp, 'm', t.nimi); tl(tp, 'v', `mediaan: ${idx.map((v) => fmt(v)).join(' → ')} ${t.uhik || ''}`); tl(tp, 'm', `keskmine: ${cs.map((c) => fmt(c.mean)).join(' → ')} ${t.uhik || ''}`); });
    }
    if (!n) h('p', { class: 'empty' }, card, 'Selles üksuses pole ühtegi teenust, millel oleks andmed kõigis kolmes seisundis.');
    const lg = h('ul', { class: 'legend' }, card);
    M.seisundid.forEach((s, i) => { const li2 = h('li', {}, lg); swatch(li2, i); h('span', {}, li2, s); });
  }

  /* ---------- Tabel ---------- */
  const COLS = [
    ['teenus', 'Teenus', (r) => D.meta.teenused[r.layer_id].nimi], ['grupp', 'Grupp', (r) => D.meta.teenused[r.layer_id].grupp],
    ['uhik', 'Ühik', (r) => D.meta.teenused[r.layer_id].uhik || ''], ['unit', 'Üksus', (r) => D.meta.uhikud[r.unit_code].nimi],
    ['pair', 'Seisundipaar', (r) => D.meta.paarid[r.pair]], ['ma', 'Mediaan (halvem)', (r) => r.median_a], ['mb', 'Mediaan (parem)', (r) => r.median_b], ['a', 'Keskmine (halvem)', (r) => r.mean_a], ['b', 'Keskmine (parem)', (r) => r.mean_b],
    ['d', 'Δ', (r) => est(r).d], ['rel', 'Δ %', (r) => est(r).rel], ['lo', 'CI alumine', (r) => est(r).lo], ['hi', 'CI ülemine', (r) => est(r).hi],
    ['p', 'p', (r) => est(r).p], ['q', 'q (FDR)', (r) => est(r).q], ['sig', 'Oluline', (r) => (est(r).sig ? 'jah' : 'ei')],
    ['n', 'Paare / plokke', (r) => (S.est === 'm' ? r.n_strata : Math.min(r.blocks_a, r.blocks_b))], ['eta', 'η² (klass)', (r) => { const e = D.meta.teenused[r.layer_id].eta2[String(D.meta.uhikud[r.unit_code].eco)]; return e ? e[0] : null; }],
  ];
  function tableRows() {
    const layers = new Set(visLayers().map((x) => x.i)), units = new Set(visUnits());
    return D.P.filter((r) => layers.has(r.layer_id) && units.has(r.unit_code) && pairsSel().includes(r.pair) && passes(r));
  }
  function table(root) {
    const card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Tabelivaade');
    h('p', { class: 'sub' }, card, 'Kõik praeguste filtritega sobivad hinnangud. Veeru päisele klõpsates sorteerub tabel. CSV sisaldab filtreeritud ridu täpsete väärtustega.');
    const rows = tableRows(), c = COLS.find((x) => x[0] === S.sort.col) || COLS.find((x) => x[0] === 'rel');
    const val = (r) => { const v = c[2](r); return v === null || v === undefined || Number.isNaN(v) ? null : v; };
    rows.sort((a, b) => { const x = val(a), y = val(b); if (x === null) return 1; if (y === null) return -1; return (typeof x === 'string' ? x.localeCompare(y, 'et') : x - y) * S.sort.dir; });
    const bar = h('div', { class: 'frow' }, card);
    const dl = h('button', { type: 'button', class: 'ghost' }, bar, `Laadi alla CSV (${rows.length} rida)`);
    dl.onclick = () => downloadCsv(rows);
    const cp = h('button', { type: 'button', class: 'ghost' }, bar, 'Kopeeri CSV');
    cp.onclick = async () => {
      const txt = csvText(rows);
      try { await navigator.clipboard.writeText(txt); cp.textContent = 'Kopeeritud'; setTimeout(() => { cp.textContent = 'Kopeeri CSV'; }, 1500); } catch {
        let ta = $('#csvbox'); if (!ta) ta = h('textarea', { id: 'csvbox', class: 'csvbox', readonly: true, 'aria-label': 'CSV' }, card);
        ta.value = txt; ta.focus(); ta.select();
      }
    };
    if (!rows.length) { h('p', { class: 'empty' }, card, 'Valitud filtritele ei vasta ühtegi tulemust.'); return; }
    const wrap = h('div', { class: 'tblwrap' }, card), t = h('table', { class: 'data' }, wrap), hd = h('tr', {}, h('thead', {}, t));
    for (const col of COLS) { const th = h('th', { 'aria-sort': S.sort.col === col[0] ? (S.sort.dir > 0 ? 'ascending' : 'descending') : 'none', tabindex: 0 }, hd, `${col[1]}${S.sort.col === col[0] ? (S.sort.dir > 0 ? ' ▲' : ' ▼') : ''}`); const f = () => { S.sort = { col: col[0], dir: S.sort.col === col[0] ? -S.sort.dir : 1 }; renderAll(true); }; th.onclick = f; th.onkeydown = (e) => { if (e.key === 'Enter') f(); }; }
    const tb = h('tbody', {}, t);
    for (const r of rows.slice(0, 500)) {
      const tr = h('tr', {}, tb), e = est(r);
      COLS.forEach((col, i) => {
        const v = col[2](r); let s;
        if (['rel'].includes(col[0])) s = pct(v, 1); else if (['p', 'q'].includes(col[0])) s = pfmt(v); else if (typeof v === 'number') s = col[0] === 'n' || col[0] === 'eta' ? nf(col[0] === 'eta' ? 2 : 0).format(v) : fmt(v); else s = v ?? '–';
        h('td', { class: col[0] === 'sig' ? (e.sig ? 'sig-y' : 'sig-n') : null }, tr, s);
      });
    }
    if (rows.length > 500) h('p', { class: 'note' }, card, `Näidatud on esimesed 500 rida ${rows.length}-st; CSV sisaldab kõiki.`);
  }
  function csvText(rows) {
    const q = (v) => (v === null || v === undefined || Number.isNaN(v) ? '' : typeof v === 'string' ? `"${v.replaceAll('"', '""')}"` : String(v));
    const head = COLS.map((c) => q(c[1])).join(',');
    return [head, ...rows.map((r) => COLS.map((c) => q(c[2](r))).join(','))].join('\n');
  }
  function downloadCsv(rows) {
    const blob = new Blob(['\ufeff', csvText(rows)], { type: 'text/csv;charset=utf-8' });
    const a = h('a', { href: URL.createObjectURL(blob), download: 'okosusteemiteenused_seisund.csv' }); document.body.append(a); a.click(); a.remove();
  }

  /* ---------- Meetod ---------- */
  function method(root) {
    const M = D.meta, p = M.parameetrid, card = h('section', { class: 'card prose' }, root);
    const P = (t) => h('p', {}, card, t);
    h('h2', {}, card, 'Meetod lühidalt');
    P('Täielik kirjeldus on repositooriumi failis docs/metoodika.md ja nõuete täitmine failis docs/lahteulesanne.md. Siin on olulisim.');
    h('h3', {}, card, 'Seisund');
    P('Seisundiklassid pärinevad baaskaardilt (2022, 5 m): „seisund_uldine” 1 = hea, 2 = keskmine, 3 = vilets. Vastavus algsetele klassidele (A–F) on iga ökosüsteemi sees erinev ja tuletati täisresolutsiooni ristiksist (iga detailne kood kaardistub täpselt ühele seisundile).');
    const t = h('table', {}, card); const hr = h('tr', {}, h('thead', {}, t)); for (const c of ['Ökosüsteem', 'hea', 'keskmine', 'vilets']) h('th', {}, hr, c);
    for (const r of [['Rohumaad', 'A, B', 'C', 'D1, D2'], ['Sood', 'A1, A2', 'B1, B2', 'C1, C2, D, E'], ['Metsad', 'A', 'A-B, A-C, B, C', 'D, E, F'], ['Põllumaad', 'A', 'B', 'C, D']]) { const tr = h('tr', {}, t); for (const c of r) h('td', {}, tr, c); }
    h('h3', {}, card, 'Tulemustabel (lähtekas): mediaan tüübi ja seisundi kaupa');
    P('Tulemustabeli väärtus on teenuse täpne pikslimediaan kogu ökosüsteemitüübi ja seisundiklassi pindala kohta, nullid kaasa arvatud: pooled pikslid on sellest väiksemad, pooled suuremad. Iga piksel on üks vaatlus ja mediaan arvutatakse kõigist pikslitest (mitte jaotuse vahemikest). Suure ökosüsteemi mediaan arvutatakse kõigi tema pikslite pealt korraga; „Asustus ja muu“ ei liideta. Keskmine on andmetes alles ja stsenaariumis kasutatakse seda pindalaga korrutamiseks, sest ainult keskmine annab koguhulga.');
    P('Valim: kihi puuduvad andmed (NoData) loetakse nulliks, kui all on baaskaardi ökosüsteem; ka teenuse kaardi ulatusest väljapoole jäävad baaskaardi pikslid on nullid. Erandid (§): mustikate ja pohlade ning kasemahla kihid, kus NoData tähendab puuduvat hinnangut ja jäetakse välja. Põllumassiivide kihtides on põldudest väljas olev ala 0, puuduv väärtus ja −1 on 0, kattuvate polügoonide korral võetakse suurim väärtus.');
    P('Märked: „ei paku“ = nullist erinevaid piksleid alla 1 % kehtivatest (lähtekasu „väga-väga vähe“; lävi on meie valik); „–“ = kehtivaid piksleid alla 5 % klassist; kaldkiri ja kollane = osaline kate; † definitsiooniline seos seisundiga; ‡ madalama lahutusvõimega kiht; § erandkiht.');
    h('h3', {}, card, 'Hinnang ja olulisus');
    P(`Muutus Δ = parema seisundi mediaan − halvema seisundi mediaan. Paaritatud hinnang võrdleb seisundite mediaane samas 1 km plokis ja samas alamökosüsteemis (kummaski vähemalt ${p.min_area_ha} ha) ning koondab plokkide erinevused kaalutud keskmisena (kaal n_a·n_b/(n_a+n_b)). See kontrollib asukoha ja alamökosüsteemi koosseisu mõju. Paaritamata hinnang on kõigi pikslite mediaanide vahe.`);
    P(`Olulisus: ${nf(0).format(p.cluster_blocks)} × ${nf(0).format(p.cluster_blocks)} km klastrite bootstrap (${nf(0).format(p.n_boot)} kordust) arvestab ruumilist autokorrelatsiooni; kahepoolsed p-väärtused korrigeeritakse Benjamini–Hochbergi meetodiga (FDR) eraldi ökosüsteemi ja alamökosüsteemi taseme jaoks (α = ${p.alpha}). Hinnang on „oluline”, kui q < ${p.alpha} ja vähemalt ${p.min_strata} paari ning ${p.min_clusters} klastrit.`);
    h('h3', {}, card, 'Piirangud, mida tuleb arvestada');
    const ul = h('ul', {}, card);
    for (const s of [
      'Statistiline olulisus ei tähenda põhjuslikkust: seisund ja teenus võivad sõltuda ühistest teguritest (mullastik, asukoht). Paaritamine vähendab, kuid ei kõrvalda seda.',
      'Osa kihte on arvutatud baaskaardi klassi või seisundi põhjal (kihi kirjelduse järgi nt kliimaregulatsioon ja kahjuritõrje; kontrollitud ka toiduteenus). Neil on muutus seisundi vahel osaliselt definitsiooniline; seda näitavad nurgamärk (η² ≥ 0,9), märk † ja hoiatus teenuse detailis.',
      'Teenuste aastad on erinevad (2020 ja 2022), baaskaart on 2022. Eraldusvõimed on 5 ja 10 m, baaskaart võetakse teenuse ruudustikule lähima naabriga.',
      'Mõnede kihtide väärtused on diskreetsed klassid või skoorid (järjestusskaala); mediaan on siis tüüpiline skoor, mitte füüsikaline suurus.',
      'Kui enamikus kohtades on teenust vähe või üldse mitte, on mediaan sageli 0. Siis näitab „mediaan kohtades, kus teenus esineb“ väärtust seal, kus teenust on.',
      'Ühikud on võetud ametlikust kihitabelist; kus tabel ühikut ei nimeta, on see tühi.',
      'Madalama lahutusvõimega kihid (930 m rastrid ja 1 km lammiruudustik) on arvutuseks viidud baaskaardi 10 m lahutusvõimele. Ühe ruudu sees on väärtus sama, seega seisundite erinevus tuleb ainult ruutude vahelistest erinevustest. Segumudel (uuriv) on teenuse detailis võrdluseks.',
    ]) h('li', {}, ul, s);
    h('p', { class: 'note' }, card, `Analüüs koostatud ${M.koostatud}. Andmeallikas: ELME kihid (KAUR). Kasutustingimused: kontrolli enne taasavaldamist.`);
  }

/*@@SECTIONS@@*/

  /* ---------- koostamine ---------- */
  function initState() {
    const M = D.meta;
    S.level = 'okosusteem'; S.ecos = new Set(M.uhikud.filter((u) => u.tase === 'okosusteem').map((u) => u.kood));
    S.alamSel = new Set(); S.alamN = 12; S.groups = new Set(M.teenused.map((t) => t.grupp)); S.props = new Set(['biofüüsikaline', 'rahaline', 'muu']);
    S.layers = new Set(M.teenused.map((t) => t.id)); S.pair = 2; S.est = 'm'; S.sig = 'all'; S.minRel = 0;
  }
  function renderAll(keep) {
    renderSections();
    const an = S.sec === 'analuus', root = $('#view');
    $('#fwrap').hidden = !an; $('#tabs').hidden = !an;
    root.replaceChildren(); tipHide();
    if (an) {
      renderFilters(keep); renderTabs();
      ({ ulevaade: heatmap, teenus: detail, profiil: profile, jaotused: distTab, kihid: layersTab, tabel: table })[S.tab](root);
      const n = tableRows().length; const c = $('#count'); if (c) c.textContent = `${n} sobivat hinnangut`;
    } else {
      ({ avaleht: homeView, tulemused: resultsView, stsenaarium: scenarioView, kvalit: qualView, lahteulesanne: briefView, vordlus: compareView, meetod: method })[S.sec](root);
    }
  }
  async function main() {
    await load(); initState();
    const best = D.P.filter((r) => D.meta.uhikud[r.unit_code].tase === 'okosusteem' && r.enough_m && r.pair === 2).sort((a, b) => (b.n_strata || 0) - (a.n_strata || 0))[0] || D.P[0];
    if (best) { S.detail.layer = best.layer_id; S.detail.unit = best.unit_code; S.profUnit = best.unit_code; }
    $('#theme').onclick = () => { const r = document.documentElement, cur = r.getAttribute('data-theme'); const dark = cur ? cur === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.setAttribute('data-theme', dark ? 'light' : 'dark'); renderAll(true); };
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => renderAll(true));
    let rt; addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => renderAll(true), 200); });
    if (innerWidth < 900) $('#fdet').open = false;
    const fromHash = () => { const k = location.hash.slice(1); if (SECTIONS.some(([x]) => x === k)) S.sec = k; };
    fromHash(); addEventListener('hashchange', () => { fromHash(); renderAll(true); });
    renderAll();
  }
  main().catch((e) => { $('#view').replaceChildren(h('p', { class: 'empty' }, null, `Andmete laadimine ebaõnnestus: ${e.message}. Ava leht veebiserveri kaudu (nt python -m http.server) või kasuta ühefailset varianti.`)); console.error(e); });
})();
