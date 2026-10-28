  /* ---------- Avaleht ---------- */
  const HEADLINE = ['puit_c_mets', 'mulla_c', 'mustikad_pohlad', 'seened', 'ohusaaste', 'tolmeldamine', 'elupaik', 'virgestus', 'erosioon_p', 'vee_regul'];
  const HOME_ECOS = [3, 31, 32, 2, 1, 4];
  const HOME_BAR_ECOS = [3, 31, 32, 2, 1, 4];
  function kRow(ok, sn) { return D.K.suured.find((r) => r[0] === ok && r[1] === sn) || null; }
  function homeView(root) {
    if (!D.K) { h('p', { class: 'empty' }, root, 'Kaasneva kasu tulemused puuduvad selles ehituses.'); return; }
    const Kd = K(), { lay } = kIndex();
    const hero = h('section', { class: 'hero' }, root);
    h('p', { class: 'eyebrow' }, hero, 'Looduse taastamise kava · kaasneva kasu hindamine');
    h('h1', {}, hero, 'Mida annab ökosüsteemi seisundi paranemine?');
    h('p', { class: 'lead' }, hero, 'Eesti maismaaökosüsteemide teenuste tüüpilised väärtused (mediaanid) viletsas, keskmises ja heas seisundis: iga ökosüsteemitüübi kohta, koos pindala, rahaliste väärtuste ja statistilise kontrolliga.');
    const act = h('div', { class: 'cta' }, hero);
    btn(act, 'Ava tulemustabel', 'btn primary', () => navTo('tulemused'));
    btn(act, 'Arvuta stsenaarium', 'btn', () => navTo('stsenaarium'));
    xlsxLink(act, 'Excel (andmetabel)').classList.replace('primary', 'ghostbtn');
    // võtmenumbrid
    const types = new Set(Kd.tuubid.filter((r) => r[3] >= 1 && r[3] <= 3).map((r) => `${r[0]}|${r[1]}`));
    const tot = Kd.suured.filter((r) => r[1] === 'kokku (hea+keskmine+vilets)' && [1, 2, 3, 4].includes(r[0])).reduce((a, r) => a + (r[2] || 0), 0);
    const pe = D.P.filter((r) => D.meta.uhikud[r.unit_code].tase === 'okosusteem' && r.pair === 2 && r.enough_m);
    const sig = pe.filter((r) => r.oluline_m_med).length;
    const stats = h('div', { class: 'kpis' }, root);
    for (const [big, small] of [[nf(0).format(types.size), 'ökosüsteemitüüpi seisundiga'], [nf(0).format(Kd.kihid.length), `teenuse kihti (${Kd.indikaatorid.length} loodushüve)`], [`${nf(1).format(tot / 100000)} tuh km²`.replace(' tuh km²', ' tuh km²'), 'maismaad seisundi hinnanguga'], [`${sig} / ${pe.length}`, 'ökosüsteemi tasandi hinnangut vilets → hea on statistiliselt olulised']]) {
      const k = h('div', { class: 'kpi' }, stats); h('div', { class: 'big' }, k, big); h('div', { class: 'sm' }, k, small);
    }
    // 1. pindala seisundi kaupa
    const c1 = h('section', { class: 'card' }, root);
    h('h2', {}, c1, 'Kui palju meil on hea, keskmist ja viletsat?');
    h('p', { class: 'sub' }, c1, 'Ökosüsteemide pindala ELME2 seisundikaardi järgi (2022). Taastamise potentsiaal on viletsa ja keskmise seisundi pindala.');
    const bars = h('div', { class: 'stackbars' }, c1);
    for (const ok of HOME_BAR_ECOS) {
      const parts = ['hea', 'keskmine', 'vilets', 'määramata'].map((s) => ({ s, a: (kRow(ok, s) || [0, 0, 0])[2] || 0 }));
      const sum = parts.reduce((a, p) => a + p.a, 0); if (!sum) continue;
      const row = h('div', { class: 'sbrow' }, bars);
      const lab = h('div', { class: 'sblab' }, row); h('b', {}, lab, ECO_SHORT[ok]); h('small', {}, lab, `${nf(0).format(sum / 1000)} tuh ha`);
      const bar = h('div', { class: 'sbar', role: 'img', 'aria-label': `${ECO_SHORT[ok]}: ${parts.map((p) => `${p.s} ${nf(0).format((p.a / sum) * 100)} %`).join(', ')}` }, row);
      for (const p of parts) {
        if (p.a <= 0) continue;
        const seg = h('div', { class: 'sseg', style: `flex:${p.a};background:${p.s === 'määramata' ? cssVar('--neutral') : stCol(p.s)}` }, bar);
        const pc = (p.a / sum) * 100;
        if (pc >= 7) h('span', { class: 'sv', style: `color:${p.s === 'keskmine' ? '#0b0b0b' : '#fff'}` }, seg, `${nf(0).format(pc)} %`);
        seg.title = `${p.s}: ${nf(0).format(p.a / 1000)} tuh ha (${nf(1).format(pc)} %)`;
      }
    }
    const lg = h('ul', { class: 'legend' }, c1);
    ['vilets', 'keskmine', 'hea'].forEach((s) => { const li = h('li', {}, lg); swatch(li, STATE_IX[s]); h('span', {}, li, s); });
    const lm = h('li', {}, lg); h('span', { class: 'sw', style: `--c:${cssVar('--neutral')}` }, lm); h('span', {}, lm, 'määramata (seisundit ei määratud)');
    // 2. mida annab paranemine
    const c2 = h('section', { class: 'card' }, root);
    h('h2', {}, c2, 'Mida annab seisundi paranemine? Vilets → hea');
    h('p', { class: 'sub' }, c2, 'Teenuse mediaan hektari kohta (nullid kaasa arvatud) viletsas ja heas seisundis ning erinevus. See on kahe seisundi võrdlus, mitte prognoos konkreetse koha taastamisest. Täielik tabel iga tüübi kohta on tulemustabelis.');
    const sc = h('div', { class: 'scroll' }, c2), t = h('table', { class: 'hm' }, sc), hd = h('tr', {}, h('thead', {}, t));
    h('th', {}, hd, 'Loodushüve');
    for (const ok of HOME_ECOS) h('th', {}, hd, ECO_SHORT[ok]);
    const tb = h('tbody', {}, t);
    for (const key of HEADLINE) {
      const ind = Kd.indikaatorid.find((i) => i.key === key); if (!ind) continue;
      const li = lay.get(ind.kihid[0]); if (li === undefined) continue; const L = Kd.kihid[li];
      const tr = h('tr', {}, tb), th = h('th', { scope: 'row' }, tr); h('b', {}, th, ind.nimi); h('small', {}, th, `${unitShort(L.uhik)}${ind.suund === 'vaiksem_parem' ? ' · väiksem on parem' : ''}`);
      for (const ok of HOME_ECOS) {
        const td = h('td', {}, tr), a = kRow(ok, 'vilets'), b = kRow(ok, 'hea');
        const ca = a && cellView(a[3][li]), cb = b && cellView(b[3][li]);
        if (!ca || !cb || ca.v === null || cb.v === null) { h('span', { class: 'hmn' }, td, ca && ca.st === ST.NONE && cb && cb.st === ST.NONE ? 'ei paku' : '–'); continue; }
        h('div', { class: 'hmv' }, td, `${fmt(ca.v)} → ${fmt(cb.v)}`);
        if (Math.abs(ca.v) > 1e-12) {
          const rel = (cb.v - ca.v) / Math.abs(ca.v), better = ind.suund === 'suurem_parem' ? rel > 0 : rel < 0;
          h('span', { class: `chg ${better ? 'up' : 'down'}`, title: better ? 'hüve kasvab' : 'hüve väheneb' }, td, `${rel > 0 ? '▲' : '▼'} ${nf(0).format(Math.abs(rel) * 100)} %`);
        }
      }
    }
    h('p', { class: 'note' }, c2, 'Nool näitab väärtuse muutust, sinine = hüve kasvab, oranž = hüve väheneb (arvestades, et nt erosiooni korral on väiksem ärakanne parem). Tähtsad piirangud: mikrokliima ja kahjuritõrje on seisundiga seotud definitsiooni tõttu, rahalised kihid ei ole summeeritavad.');
    btn(c2, 'Vaata kõiki teenuseid ja tüüpe →', 'btn', () => navTo('tulemused'));
    // 3. kolm sammu
    const c3 = h('section', { class: 'steps' }, root);
    for (const [n, title, txt, go, lab] of [
      ['1', 'Seisund', 'ELME2 baaskaart jagab ökosüsteemid kolme seisundiklassi: hea, keskmine, vilets (lisaks määramata ja hindamata). Klassid vastavad algsetele A–F tähistele ökosüsteemi kaupa.', 'meetod', 'Vaata, kuidas seisund on määratud'],
      ['2', 'Mediaan', 'Iga ökosüsteemitüübi ja seisundi kohta on arvutatud teenuse mediaan kogu klassi pindala kohta: pooled pikslid on sellest väiksemad, pooled suuremad. Nullid lähevad arvesse. Pindalaga korrutamiseks kasutab stsenaarium keskmist.', 'tulemused', 'Ava tulemustabel'],
      ['3', 'Muutus ja kindlus', 'Seisundite erinevust kontrollitakse paaritatud hinnangu ja ruumilise bootstrapiga. Stsenaariumi kalkulaator rakendab selle ühele tüübile ja pindalale.', 'stsenaarium', 'Ava kalkulaator'],
    ]) {
      const s = h('article', { class: 'step' }, c3); h('span', { class: 'n' }, s, n); h('h3', {}, s, title); h('p', {}, s, txt);
      const a = h('a', { href: `#${go}` }, s, `${lab} →`); a.onclick = (e) => { e.preventDefault(); navTo(go); };
    }
    // 4. töö seis
    const N = D.N; if (N) {
      const c4 = h('section', { class: 'card' }, root);
      h('h2', {}, c4, 'Lähteülesande täitmine');
      const count = (st) => N.nouded.filter((r) => r.staatus === st).length;
      const row = h('div', { class: 'progress' }, c4);
      for (const [st, cls, txt] of [['täidetud', 'done', 'täidetud'], ['osaliselt', 'part', 'osaliselt'], ['ootel', 'wait', 'ootab välist sisendit'], ['ei ole tehtud', 'todo', 'tegemata']]) {
        const p = h('div', { class: `prog ${cls}` }, row); h('b', {}, p, String(count(st))); h('span', {}, p, txt);
      }
      h('p', { class: 'sub' }, c4, 'Kvantitatiivne osa (mediaanid ja keskmised tüübi ja seisundi kaupa) on valmis. Tegevuste koondtabelit ei saa täita enne, kui Kliimaministeerium annab kinnitatud meetmete nimekirja; selleks on mall ja teenuste kaupa tõendusbaas. Lõppraporti tähtaeg on 4. november 2026.');
      btn(c4, 'Vaata nõuete täitmist ja kriitilisi tähelepanekuid →', 'btn', () => navTo('lahteulesanne'));
    }
    h('p', { class: 'note home-note' }, root, `Allikas: ELME/ELME2 kaardikihid (Keskkonnaagentuur), baaskaart 2022. Andmed on modelleeritud kihid, mitte mõõtmised. Tulemus on esialgne versioon tagasisideks (${D.meta.koostatud}). Enne taasavaldamist kontrolli andmete litsentsi.`);
  }
