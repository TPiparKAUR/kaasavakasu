  /* ---------- Tulemustabel (lähtekasu tabel) ---------- */
  function ktInit() {
    const Kd = K();
    S.kt = {
      view: 'tuubid', eco: new Set([1, 2, 3, 31, 32, 4, 5]), seis: new Set(['hea', 'keskmine', 'vilets']), sekt: new Set(Kd.indikaatorid.map((i) => i.sektsioon)),
      omadus: new Set(['biofüüsikaline', 'rahaline', 'muu']), q: '', kokku: true, ind: new Set(Kd.indikaatorid.map((i) => i.key)),
    };
  }
  function ktLayers() {
    const { ind } = kIndex();
    return D.K.kihid.map((l, i) => ({ l, i, I: ind.get(l.ind) })).filter(({ l, I }) => S.kt.sekt.has(I.sektsioon) && S.kt.omadus.has(l.omadus || 'muu') && S.kt.ind.has(l.ind));
  }
  function ktRows() {
    const k = S.kt;
    if (k.view === 'tuubid') {
      const q = k.q.trim().toLowerCase();
      return D.K.tuubid.filter((r) => k.eco.has(r[0]) && k.seis.has(r[4]) && (!q || r[2].toLowerCase().includes(q)));
    }
    return D.K.suured.filter((r) => k.eco.has(r[0]) && (k.seis.has(r[1]) || (k.kokku && r[1].startsWith('kokku'))));
  }
  function ktToCsv(rows, lays) {
    const head = ['Ökosüsteem', ...(S.kt.view === 'tuubid' ? ['Tüüp'] : []), 'Seisund', 'Pindala (ha)', ...lays.map(({ l }) => `${l.nimi} [${unitShort(l.uhik) || 'ühik puudub'}]`)];
    const body = rows.map((r) => {
      const first = S.kt.view === 'tuubid' ? [D.K.eco[r[0]], r[2], r[4], r[5]] : [D.K.suured_nimed[r[0]] || D.K.eco[r[0]], r[1], r[2]];
      const cells = (S.kt.view === 'tuubid' ? r[6] : r[3]);
      return [...first, ...lays.map(({ i }) => { const v = cellView(cells[i]); return v.v !== null ? v.v : v.txt; })].map(csvQ).join(',');
    });
    return [head.map(csvQ).join(','), ...body].join('\n');
  }
  function resultsView(root) {
    if (!D.K) { h('p', { class: 'empty' }, root, 'Kaasneva kasu tulemused puuduvad.'); return; }
    if (!S.kt) ktInit();
    const k = S.kt, Kd = K();
    const card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Tulemustabel: teenuse mediaan ökosüsteemitüübi ja seisundi kaupa');
    h('p', { class: 'sub' }, card, 'Iga rida on ELME2 ökosüsteemitüüp ja seisundiklass (või suur ökosüsteem). Väärtus on teenuse täpne mediaan kogu klassi pindala kohta, nullid kaasa arvatud (pooled pikslid on sellest väiksemad, pooled suuremad). Keskmine ja mediaan kohtades, kus teenus esineb, on lahtri kohtspikris. Tabel vastab Keskkonnaagentuuri lähtekasule; sama sisu on Exceli failis.');
    const bar = h('div', { class: 'tools' }, card);
    h('span', { class: 'tl' }, bar, 'Rida');
    const sg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Tabeli tüüp' }, bar);
    for (const [v, t] of [['tuubid', 'Tüübid × seisund'], ['suured', 'Suured ökosüsteemid']]) { const b = h('button', { type: 'button', 'aria-pressed': String(k.view === v) }, sg, t); b.onclick = () => { k.view = v; renderAll(true); }; }
    xlsxLink(bar, 'Excel');
    // filtrid
    const f = h('div', { class: 'frow kfilters' }, card);
    const chipsRow = (label, items, set) => {
      const g = h('div', { class: 'fgrp' }, f); h('span', { class: 'lbl' }, g, label);
      const c = h('div', { class: 'chips' }, g);
      for (const [v, t] of items) { const b = h('button', { type: 'button', class: 'chip', 'aria-pressed': String(set.has(v)) }, c, t); b.onclick = () => { set.has(v) ? set.delete(v) : set.add(v); renderAll(true); }; }
      return g;
    };
    chipsRow('Ökosüsteem', [[3, 'Mets'], ...(k.view === 'suured' ? [[31, 'Kuivad metsad'], [32, 'Märjad metsad']] : []), [2, 'Soo'], [1, 'Niit'], [4, 'Põld'], [5, 'Rannik'], ...(k.view === 'tuubid' ? [[6, 'Asustus ja muu']] : [])], k.eco);
    chipsRow('Seisund', [['hea', 'hea'], ['keskmine', 'keskmine'], ['vilets', 'vilets'], ['määramata', 'määramata'], ['hindamata', 'hindamata (rannik, muu)']], k.seis);
    chipsRow('Teenuse liik', [...new Set(Kd.indikaatorid.map((i) => i.sektsioon))].map((x) => [x, x]), k.sekt);
    chipsRow('Väärtus', [['biofüüsikaline', 'biofüüsikaline'], ['rahaline', 'rahaline'], ['muu', 'indeks / skoor']], k.omadus);
    if (k.view === 'tuubid') {
      const g = h('div', { class: 'fgrp' }, f); h('label', { for: 'ktq', class: 'lbl' }, g, 'Otsi tüüpi');
      const q = h('input', { type: 'search', id: 'ktq', placeholder: 'nt rannaniidud, palumets', value: k.q, class: 'srch' }, g);
      q.oninput = () => { k.q = q.value; clearTimeout(q._t); q._t = setTimeout(() => { renderAll(true); const e = $('#ktq'); if (e) { e.focus(); e.setSelectionRange(e.value.length, e.value.length); } }, 250); };
    } else {
      const g = h('div', { class: 'fgrp' }, f); const lb = h('label', { class: 'chk' }, g), cb = h('input', { type: 'checkbox' }, lb); cb.checked = k.kokku; h('span', {}, lb, 'Näita „kokku“ ridu'); cb.onchange = () => { k.kokku = cb.checked; renderAll(true); };
    }
    // indikaatorite valik
    const dd = h('details', { class: 'dd' }, f); h('summary', { class: 'sel' }, dd, `Teenused ${k.ind.size}/${Kd.indikaatorid.length}`);
    const pn = h('div', { class: 'dd-panel' }, dd); const acts = h('div', { class: 'acts' }, pn);
    btn(acts, 'Vali kõik', 'ghost', () => { Kd.indikaatorid.forEach((i) => k.ind.add(i.key)); renderAll(true); });
    btn(acts, 'Tühjenda', 'ghost', () => { k.ind.clear(); renderAll(true); });
    for (const i of Kd.indikaatorid) { const r = h('label', { class: 'row' }, pn), cb = h('input', { type: 'checkbox' }, r); cb.checked = k.ind.has(i.key); cb.onchange = () => { cb.checked ? k.ind.add(i.key) : k.ind.delete(i.key); renderAll(true); }; h('span', {}, r, i.nimi); }
    const rows = ktRows(), lays = ktLayers();
    h('p', { class: 'count-line' }, card, `${rows.length} rida × ${lays.length} teenuse kihti`);
    btn(bar, 'CSV (praegune vaade)', 'btn', () => saveText('kaasnev_tulemustabel.csv', ktToCsv(rows, lays)));
    if (!rows.length || !lays.length) { h('p', { class: 'empty' }, card, 'Valitud filtritele ei vasta ühtegi rida.'); return; }
    // tabel
    const wrap = h('div', { class: 'tblwrap rt-wrap' }, card), t = h('table', { class: 'rt' }, wrap);
    const th = h('thead', {}, t), r1 = h('tr', {}, th), r2 = h('tr', {}, th), r3 = h('tr', {}, th);
    const fixed = k.view === 'tuubid' ? ['Tüüp', 'Seisund', 'Pindala (ha)'] : ['Ökosüsteem', 'Seisund', 'Pindala (ha)'];
    fixed.forEach((x, c) => { h('th', { class: `fx fx${c}`, rowspan: 3, scope: 'col' }, r1, x); });
    const groups = []; for (const x of lays) { const g = groups[groups.length - 1]; if (g && g.ind === x.l.ind) g.n++; else groups.push({ ind: x.l.ind, n: 1, I: x.I }); }
    for (const g of groups) h('th', { colspan: g.n, class: 'gh', scope: 'colgroup', title: g.I.grupp }, r1, g.I.nimi);
    for (const x of lays) {
      const e = h('th', { class: `lh ${x.l.roll}`, scope: 'col' }, r2, x.l.nimi.length > 54 ? `${x.l.nimi.slice(0, 52)}…` : x.l.nimi);
      e.title = `${x.l.nimi}${flagsOf(x.l)}`;
      if (flagsOf(x.l)) h('sup', {}, e, flagsOf(x.l));
      h('div', { class: 'rl' }, e, x.l.roll === 'raha' ? 'rahaline' : x.l.roll === 'lisa' ? 'lisakiht' : 'biofüüsikaline');
      h('th', { class: 'uh', scope: 'col' }, r3, unitShort(x.l.uhik) || 'ühik puudub');
    }
    const tb = h('tbody', {}, t); let lastEco = null;
    rows.forEach((r, ri) => {
      const eco = r[0];
      if (k.view === 'tuubid' && eco !== lastEco) { const gr = h('tr', { class: 'grp' }, tb); h('th', { colspan: 3 + lays.length }, gr, Kd.eco[String(eco)]); lastEco = eco; }
      const tr = h('tr', { class: 'dr' }, tb), cells = k.view === 'tuubid' ? r[6] : r[3];
      const sn = k.view === 'tuubid' ? r[4] : r[1], area = k.view === 'tuubid' ? r[5] : r[2];
      const c0 = h('th', { class: 'fx fx0', scope: 'row' }, tr, k.view === 'tuubid' ? r[2] : (Kd.suured_nimed[String(eco)] || Kd.eco[String(eco)]));
      if (k.view === 'tuubid') { c0.tabIndex = 0; c0.classList.add('lnk'); c0.title = 'Ava stsenaariumi kalkulaatoris'; const go = () => { S.calc = { ...(S.calc || {}), key: `t:${r[0]}|${r[1]}` }; navTo('stsenaarium'); }; c0.onclick = go; c0.onkeydown = (e) => { if (e.key === 'Enter') go(); }; }
      const c1 = h('td', { class: 'fx fx1' }, tr); h('span', { class: 'sdot', style: `background:${stCol(sn)}` }, c1); h('span', {}, c1, sn);
      h('td', { class: 'fx fx2 num' }, tr, nf(0).format(area || 0));
      lays.forEach(({ i }, ci) => { const v = cellView(cells[i]); h('td', { class: `num ${v.cls}`, 'data-r': ri, 'data-c': ci }, tr, v.txt); });
    });
    tb.addEventListener('pointermove', (e) => { const td = e.target.closest('td[data-r]'); if (!td) { tipHide(); return; } const r = rows[+td.dataset.r], x = lays[+td.dataset.c]; tipShow((tp) => cellTip(tp, r, x), e, td); });
    tb.addEventListener('pointerleave', tipHide);
    statusLegend(card);
    h('p', { class: 'note' }, card, '† seos seisundiga on osaliselt definitsiooniline; ‡ madalama lahutusvõimega kiht (930 m / 1 km), viidud 10 m lahutusvõimele; § erandkiht: puuduvad andmed on valimist välja jäetud (mustikad, pohlad, kasemahl). Rahalised kihid on osalt riigi aastase kogusumma jaotus, osalt varu ja osalt aastane voog; ära summeeri teenuseid ega biofüüsikalist ja rahalist versiooni (vt Kvalitatiivne).');
  }
  function cellTip(tp, r, x) {
    const k = S.kt, tuubid = k.view === 'tuubid', cells = tuubid ? r[6] : r[3], c = cells[x.i];
    tl(tp, 'm', `${tuubid ? r[2] : (D.K.suured_nimed[String(r[0])] || D.K.eco[String(r[0])])} · ${tuubid ? r[4] : r[1]}`);
    tl(tp, 'm', `${x.l.nimi}${flagsOf(x.l)}`);
    if (!c) { tl(tp, 'm', 'andmeid pole'); return; }
    const [med, mean, kate, esineb, st, mednz] = c, name = D.K.staatused[st];
    if (name === 'ei paku') { tl(tp, 'v', 'ei paku teenust'); tl(tp, 'm', `nullist erinevaid piksleid ${esineb === null ? '–' : nf(2).format(esineb * 100)} % kehtivatest (lävi 1 %)`); return; }
    if (med === null) { tl(tp, 'v', 'teenust ei hinnatud'); tl(tp, 'm', `kehtivaid piksleid ${kate === null ? '–' : nf(1).format(kate * 100)} % klassist`); return; }
    tl(tp, 'v', `mediaan ${fmt(med)} ${unitShort(x.l.uhik)}`);
    tl(tp, 'm', `keskmine ${fmt(mean)} · mediaan kohtades, kus teenus esineb: ${fmt(mednz)}`);
    if (kate !== null) tl(tp, 'm', `kehtivaid piksleid ${nf(1).format(kate * 100)} %; nullist erinevaid ${nf(0).format((esineb || 0) * 100)} %`);
    if (x.l.madal_lahutus) tl(tp, 'm', '‡ madalama lahutusvõimega kiht, viidud 10 m lahutusvõimele');
    if (x.l.nodata_valja) tl(tp, 'm', '§ erandkiht: puuduvad andmed on valimist välja jäetud');
  }
