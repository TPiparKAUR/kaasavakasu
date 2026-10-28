  /* ---------- Stsenaarium: vilets/keskmine → parem seisund etteantud pindalal ---------- */
  function calcUnits() {
    const Kd = K(), out = [];
    for (const ok of [3, 31, 32, 2, 1, 4]) {
      out.push({ key: `e:${ok}`, label: `${ECO_SHORT[ok]}: kõik tüübid kokku`, eco: ok, alam: null, group: ECO_SHORT[ok === 31 || ok === 32 ? 3 : ok] });
    }
    const seen = new Set();
    for (const r of Kd.tuubid) {
      if (r[3] < 1 || r[3] > 3) continue; const key = `t:${r[0]}|${r[1]}`; if (seen.has(key)) continue; seen.add(key);
      out.push({ key, label: r[2], eco: r[0], alam: r[1], group: ECO_SHORT[r[0]] });
    }
    return out;
  }
  function calcStates(u) {
    const Kd = K(), have = new Set();
    if (u.alam === null) for (const r of Kd.suured) { if (r[0] === u.eco) have.add(r[1]); }
    else for (const r of Kd.tuubid) { if (r[0] === u.eco && r[1] === u.alam) have.add(r[4]); }
    return ['vilets', 'keskmine', 'hea'].filter((s) => have.has(s));
  }
  function calcRow(u, state) {
    const Kd = K();
    if (u.alam === null) { const r = Kd.suured.find((x) => x[0] === u.eco && x[1] === state); return r ? { area: r[2], cells: r[3] } : null; }
    const r = Kd.tuubid.find((x) => x[0] === u.eco && x[1] === u.alam && x[4] === state); return r ? { area: r[5], cells: r[6] } : null;
  }
  function buildTE() {
    if (D.TE) return D.TE;
    D.TE = new Map(); const T = D.T;
    if (T && T.rows) for (const r of T.rows) { const o = Object.fromEntries(T.cols.map((c, i) => [c, r[i]])); D.TE.set(`${o.tase}|${o.uksus}|${o.kiht}|${o.paar}`, o); }
    return D.TE;
  }
  function evidenceFor(u, layer, pair) {
    buildTE();
    const eu = u.alam === null ? D.meta.uhikud.find((x) => x.tase === 'okosusteem' && x.kood === u.eco) : null;
    if (u.alam === null && !eu) return null;
    const name = eu ? eu.nimi : u.label;
    return D.TE.get(`${u.alam === null ? 'okosusteem' : 'alam'}|${name}|${layer}|${pair}`) || null;
  }
  function additiveUnit(l) {
    const u = unitShort(l.uhik);
    if (!/\/ha/.test(u) || /0,01 ha/.test(u)) return null;
    return u.replace('/ha', '');
  }
  function scenarioView(root) {
    if (!D.K) { h('p', { class: 'empty' }, root, 'Kaasneva kasu tulemused puuduvad.'); return; }
    const units = calcUnits(); if (!S.calc) S.calc = {};
    const c = S.calc; if (!c.key) c.key = units.find((x) => x.key.startsWith('t:3|'))?.key || units[0].key;
    if (!units.some((x) => x.key === c.key)) c.key = units[0].key;
    const u = units.find((x) => x.key === c.key), have = calcStates(u);
    c.from = have.includes(c.from) && c.from !== 'hea' ? c.from : have.includes('vilets') ? 'vilets' : have[0];
    const goals = have.filter((s) => ['keskmine', 'hea'].includes(s) && ['vilets', 'keskmine', 'hea'].indexOf(s) > ['vilets', 'keskmine', 'hea'].indexOf(c.from));
    c.to = goals.includes(c.to) ? c.to : goals[goals.length - 1] || null;
    c.ha = Number.isFinite(c.ha) && c.ha > 0 ? c.ha : 1000;
    const card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Stsenaarium: mida annaks seisundi paranemine kindlal pindalal?');
    h('p', { class: 'sub' }, card, 'Vali ökosüsteemitüüp, praegune ja eesmärgiks olev seisund ning pindala. Tabel näitab teenuse mediaane ja nende vahet hektari kohta. Pindalaga korrutamiseks kasutatakse keskmiste vahet, sest ainult keskmine annab koguhulga (mediaan korda pindala ei ole koguhulk). See on kahe seisundi võrdlus Eesti tasandil, mitte prognoos konkreetse koha kohta ega ajastus (taastumine võtab aega).');
    const ctl = h('div', { class: 'frow' }, card);
    const g1 = h('div', { class: 'fgrp wide' }, ctl); h('label', { for: 'cu', class: 'lbl' }, g1, 'Ökosüsteem / tüüp');
    const su = h('select', { id: 'cu' }, g1); let lastG = null, og = null;
    for (const x of units) { if (x.group !== lastG) { og = h('optgroup', { label: x.group }, su); lastG = x.group; } const o = h('option', { value: x.key }, og, x.label); if (x.key === c.key) o.selected = true; }
    su.onchange = () => { c.key = su.value; renderAll(true); };
    const g2 = h('div', { class: 'fgrp' }, ctl); h('label', { for: 'cf', class: 'lbl' }, g2, 'Praegune seisund');
    const sf = h('select', { id: 'cf' }, g2); for (const s of have.filter((x) => x !== 'hea')) { const o = h('option', { value: s }, sf, s); if (s === c.from) o.selected = true; }
    sf.onchange = () => { c.from = sf.value; renderAll(true); };
    const g3 = h('div', { class: 'fgrp' }, ctl); h('label', { for: 'ct', class: 'lbl' }, g3, 'Eesmärk');
    const st = h('select', { id: 'ct' }, g3); for (const s of goals) { const o = h('option', { value: s }, st, s); if (s === c.to) o.selected = true; }
    st.onchange = () => { c.to = st.value; renderAll(true); };
    const g4 = h('div', { class: 'fgrp' }, ctl); h('label', { for: 'ch', class: 'lbl' }, g4, 'Pindala (ha)');
    const ha = h('input', { id: 'ch', type: 'number', min: 0, step: 'any', value: c.ha, class: 'num-in' }, g4); ha.onchange = () => { c.ha = parseFloat(ha.value); renderAll(true); };
    if (!c.to) { h('p', { class: 'empty' }, card, 'Sellel tüübil ei ole piisavalt seisundeid (vähemalt kaks) stsenaariumi jaoks.'); return; }
    const A = calcRow(u, c.from), B = calcRow(u, c.to);
    const sub = h('p', { class: 'note' }, card);
    sub.append(`Võrdluse pindalad (baaskaart): ${c.from} ${nf(0).format(A.area)} ha, ${c.to} ${nf(0).format(B.area)} ha. `);
    if (c.ha > A.area) h('b', { class: 'warnx' }, sub, `Sisestatud pindala ületab praeguse seisundi pindala Eestis (${nf(0).format(A.area)} ha).`);
    const sc = h('div', { class: 'tblwrap' }, card), t = h('table', { class: 'data scn' }, sc), hd = h('tr', {}, h('thead', {}, t));
    for (const x of ['Loodushüve', 'Ühik', `${c.from} (mediaan)`, `${c.to} (mediaan)`, 'Mediaanide vahe hektari kohta', 'Keskmiste vahe hektari kohta', `Muutus ${nf(0).format(c.ha)} ha kohta (keskmiste järgi)`, 'Hüve', 'Paaritatud hinnang (kontroll)', 'Tähelepanek']) h('th', {}, hd, x);
    const tb = h('tbody', {}, t), Kd = K(), pair = `${c.from}→${c.to}`;
    for (const ind of Kd.indikaatorid) {
      for (const lid of ind.kihid) {
        const li = Kd.kihid.findIndex((x) => x.id === lid), L = Kd.kihid[li];
        const a = cellView(A.cells[li]), b = cellView(B.cells[li]);
        if (a.st === null && b.st === null) continue;
        const tr = h('tr', {}, tb);
        const c0 = h('td', {}, tr); h('b', {}, c0, ind.nimi); h('small', {}, c0, ` ${L.roll === 'raha' ? 'rahaline' : L.roll === 'lisa' ? 'lisakiht' : 'biofüüsikaline'}${flagsOf(L)}`);
        h('td', {}, tr, unitShort(L.uhik) || '–');
        const fail = (v) => v.v === null;
        h('td', { class: `num ${a.cls}` }, tr, a.txt); h('td', { class: `num ${b.cls}` }, tr, b.txt);
        if (fail(a) || fail(b)) { for (let i = 0; i < 5; i++) h('td', {}, tr, '–'); h('td', {}, tr, a.st === ST.NONE && b.st === ST.NONE ? 'mõlemas seisundis ei paku' : 'ühes seisundis puudub'); continue; }
        const signed = (v) => (v === 0 ? '0' : `${v > 0 ? '+' : '−'}${fmt(Math.abs(v))}`);
        const dm = b.v - a.v; h('td', { class: 'num strong' }, tr, signed(dm));
        const d = a.mean !== null && b.mean !== null ? b.mean - a.mean : null;
        h('td', { class: 'num' }, tr, d === null ? '–' : signed(d));
        const tu = additiveUnit(L);
        h('td', { class: 'num strong' }, tr, tu && d !== null ? `${d > 0 ? '+' : d < 0 ? '−' : ''}${fmt(Math.abs(d) * c.ha)} ${tu}` : '–');
        // suund keskmiste järgi (sama mis koguhulgal); kui keskmist pole, mediaanide järgi
        const dd = d === null ? dm : d;
        const better = dd === 0 ? null : ind.suund === 'suurem_parem' ? dd > 0 : dd < 0;
        const hv = h('td', {}, tr); h('span', { class: `chg ${better === null ? '' : better ? 'up' : 'down'}` }, hv, better === null ? 'muutus puudub' : better ? '▲ kasvab' : '▼ väheneb');
        const ev = evidenceFor(u, lid, pair), te = h('td', {}, tr);
        if (ev && ev.hinnang) { h('span', { class: `pill ${ev.oluline ? 'sig' : ''}` }, te, `${ev.hinnang}: ${sgnRel(ev.rel)}${ev.oluline ? ' · oluline' : ' · ei ole oluline'}`); } else h('span', { class: 'muted' }, te, '–');
        const notes = h('div', { class: 'flagcell' }, h('td', {}, tr));
        if (ind.tuup === 'varu') pill(notes, 'varu', 'pinfo', 'Väärtus on varu, mitte aastane voog');
        if (ind.tuup === 'voog') pill(notes, 'aastane voog', 'pinfo', 'Aastane voog');
        if (ind.tuup === 'indeks' || ind.tuup === 'skoor') pill(notes, ind.tuup, 'pinfo', 'Ei ole liidetav hektarite kaupa');
        if (L.roll === 'raha' && /^piiratud/.test(ind.kulukasu)) pill(notes, 'kogusumma jaotus', 'warn', ind.kulukasu);
        if (L.definitsiooniline) pill(notes, '† definitsiooniline', 'warn', 'Seos seisundiga on osaliselt definitsiooniline');
        if (L.madal_lahutus) pill(notes, '‡ madalam lahutusvõime', 'warn', 'Kiht on 930 m / 1 km lahutusvõimega ja viidud 10 m lahutusvõimele');
        if (L.nodata_valja) pill(notes, '§ erandkiht', 'pinfo', 'Puuduvad andmed on valimist välja jäetud');
        if (L.roll === 'raha' && /hind kokku/.test(ind.kulukasu + L.tabeli_markus)) pill(notes, 'hind kokku leppida', 'warn', 'Kihitabeli märkus');
      }
    }
    h('p', { class: 'note' }, card, 'Mediaanide vahe näitab tüüpilise koha muutust. Pindala kohta muutus = (eesmärgiseisundi keskmine − praeguse seisundi keskmine) × pindala (kogu klassi pindala kohta, nullid kaasa arvatud). Ära summeeri ridu: biofüüsikaline ja rahaline versioon on sama hüve; rahalised kihid on osalt riigi aastase kogusumma jaotus (muutust ei teki), osalt varu (EUR) ja osalt aastane voog (EUR/a). Paaritatud hinnang on sama seisundipaari erinevus samas 1 km plokis ja alamökosüsteemis; kui see erineb oluliselt tabeli vahest, mõjutab erinevust asukoht, mitte seisund.');
    statusLegend(card);
  }
  function sgnRel(r) { return r === null || r === undefined ? '–' : `${r > 0 ? '+' : r < 0 ? '−' : ''}${nf(0).format(Math.abs(r) * 100)} %`; }
