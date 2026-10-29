  /* ---------- Kvalitatiivne raamistik ---------- */
  function qEvidence(ind, ecoCode) {
    // ökosüsteemi tasandi tõendus vilets → hea kihi kaupa; võtame indikaatori esimese kihi, mille kohta on tõendus
    buildTE();
    const name = D.meta.uhikud.find((x) => x.tase === 'okosusteem' && x.kood === ecoCode)?.nimi;
    for (const lid of ind.kihid) { const e = D.TE.get(`okosusteem|${name}|${lid}|vilets→hea`); if (e && e.hyve_suund) return { e, lid }; }
    return null;
  }
  function qualView(root) {
    if (!D.K) { h('p', { class: 'empty' }, root, 'Tulemused puuduvad.'); return; }
    const Kd = K(), card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Kvalitatiivne hindamine: raamistik ja tõendusbaas');
    h('p', { class: 'sub' }, card, 'Lähteülesande järgi hinnatakse iga otseselt loodushüvesid mõjutava tegevuse suunda, tugevust, ajalist avaldumist ja ulatust ning seost äärmuslike ilmastikunähtustega. Tegevusi ei saa täita enne, kui Kliimaministeerium kinnitab meetmete nimekirja. Siin on valmis teenuste kaupa raamistik ja andmetest tulenev tõendus, millelt tegevuspõhist hinnangut saab ette valmistada.');
    h('p', { class: 'warn' }, card, 'Ajaraam, ulatus, seos äärmusnähtustega, kasutatavus kulu-kasu võrdluses, topeltarvestus ja tugevuse lävendid on ETTEPANEKUD kihtide kirjelduse ja tabeli märkuste põhjal. Eksperdid ei ole neid valideerinud ja CICES-i klasside koode ei ole lähteandmetes.');
    // sammud
    const steps = h('ol', { class: 'qsteps' }, card);
    for (const t of ['Meetmete ja tegevuste valik (KLIM kinnitab) – ootel', 'Loodushüvede seostamine tegevusega (CICES v5.1 sektsioonid on määratud, rühmad on ettepanek)', 'Mõju suund ja tugevus: andmepõhine tõendus vilets → hea (allpool)', 'Ajaraam, ulatus, äärmusnähtused, topeltarvestus, ebakindlus: teenuste ettepanekud (allpool), ekspert kinnitab', 'Tegevuste koondtabel (13 veergu) Exceli mallina']) h('li', {}, steps, t);
    // filter
    const sects = [...new Set(Kd.indikaatorid.map((i) => i.sektsioon))];
    if (!S.qs) S.qs = { sekt: new Set(sects), open: new Set() };
    const bar = h('div', { class: 'tools' }, card); h('span', { class: 'tl' }, bar, 'CICES sektsioon');
    const c = h('div', { class: 'chips' }, bar);
    for (const s of sects) { const b = h('button', { type: 'button', class: 'chip', 'aria-pressed': String(S.qs.sekt.has(s)) }, c, s); b.onclick = () => { S.qs.sekt.has(s) ? S.qs.sekt.delete(s) : S.qs.sekt.add(s); renderAll(true); }; }
    xlsxLink(bar, 'Excel (sh tegevuste koondtabeli mall)');
    // tabel: indikaator + ökosüsteemi tõendus
    const wrap = h('div', { class: 'qlist' }, card);
    const head = h('div', { class: 'qrow qhead' }, wrap);
    h('div', {}, head, 'Loodushüve'); for (const ok of [3, 2, 1, 4]) h('div', { class: 'qe' }, head, ECO_SHORT[ok]);
    for (const ind of Kd.indikaatorid.filter((i) => S.qs.sekt.has(i.sektsioon))) {
      const det = h('details', { class: 'qitem' }, wrap); if (S.qs.open.has(ind.key)) det.open = true;
      det.ontoggle = () => { det.open ? S.qs.open.add(ind.key) : S.qs.open.delete(ind.key); };
      const sm = h('summary', { class: 'qrow' }, det), nm = h('div', { class: 'qn' }, sm);
      h('b', {}, nm, ind.nimi); h('small', {}, nm, `${ind.sektsioon} · ${ind.tuup === 'varu' ? 'varu' : ind.tuup === 'voog' ? 'aastane voog' : ind.tuup}${ind.suund === 'vaiksem_parem' ? ' · väiksem väärtus on parem' : ''}${ind.kihid.some((id) => Kd.kihid.find((l) => l.id === id)?.madal_lahutus) ? ' · madalam lahutusvõime (930 m / 1 km)' : ''}`);
      for (const ok of [3, 2, 1, 4]) {
        const td = h('div', { class: 'qe' }, sm), q = qEvidence(ind, ok);
        if (!q) { h('span', { class: 'qb none', title: 'tõendust ei ole (teenus ei esine või ei piisa andmeid)' }, td, '–'); continue; }
        const e = q.e, cls = e.hyve_suund === 'positiivne' ? 'up' : e.hyve_suund === 'negatiivne' ? 'down' : 'unk';
        const sym = e.hyve_suund === 'positiivne' ? '▲' : e.hyve_suund === 'negatiivne' ? '▼' : '○';
        const b = h('span', { class: `qb ${cls}`, title: `${e.hinnang}: ${sgnRel(e.rel)} (${e.oluline ? 'oluline' : 'ei ole oluline'}); kiht ${q.lid}` }, td, `${sym} ${e.tugevus || ''}`.trim()); void b;
      }
      const body = h('dl', { class: 'qdl' }, det);
      const row = (k, v) => { if (!v) return; h('dt', {}, body, k); h('dd', {}, body, v); };
      row('CICES rühm (ettepanek)', ind.grupp); row('Ajaline raamistik (ettepanek)', ind.ajaraam); row('Ulatus (ettepanek)', ind.ulatus);
      row('Äärmuslikud ilmastikunähtused', ind.ekstreem); row('Rahalise väärtuse meetod', ind.raha_meetod); row('Kasutatavus kulu-kasu võrdluses', ind.kulukasu);
      row('Topeltarvestuse risk', ind.topelt); row('Ebakindlus', ind.ebakindlus); row('Märkus sotsiaalmajandusliku mõju hindajale', ind.markus);
      row('Kihid', ind.kihid.join(', '));
    }
    const lg = h('ul', { class: 'legend' }, card);
    for (const [cls, t] of [['up', '▲ positiivne: hüve kasvab vilets → hea (oluline, FDR q < 0,05)'], ['down', '▼ negatiivne: hüve väheneb'], ['unk', '○ ebaselge: ei ole oluline või ei piisa andmeid'], ['none', '– tõendust ei ole']]) { const li = h('li', {}, lg); h('span', { class: `qb ${cls}` }, li, cls === 'up' ? '▲' : cls === 'down' ? '▼' : cls === 'unk' ? '○' : '–'); h('span', {}, li, t); }
    h('p', { class: 'note' }, card, `Tugevuse ettepanek (nõrk, keskmine, tugev) lähtub suhtelisest muutusest: nõrk alla ${Math.round(Kd.parameetrid.tugevuse_lavendid[0] * 100)} %, keskmine alla ${Math.round(Kd.parameetrid.tugevuse_lavendid[1] * 100)} %, tugev vähemalt ${Math.round(Kd.parameetrid.tugevuse_lavendid[1] * 100)} %. Lävendid ei tule andmetest; need tuleb eksperdiga kokku leppida. Suund arvestab, et mõne teenuse korral on väiksem väärtus parem (nt erosiooni ärakanne). Seisund on ruumiline võrdlus, mitte taastamise tulemus.`);
    // mall
    const c2 = h('section', { class: 'card' }, root);
    h('h2', {}, c2, 'Tegevuste koondtabeli mall');
    h('p', { class: 'sub' }, c2, 'Lähteülesande järgi esitatakse iga otseselt loodushüvesid mõjutava tegevuse kohta vähemalt allolevad andmed. Mall on Exceli failis (leht „Tegevuste koondtabel (mall)“, rippmenüüdega); täitmist ootab KLIMi meetmete nimekiri.');
    const ul = h('ul', { class: 'cols' }, c2);
    for (const [n, d] of [['Meede või tegevus', 'KLIMi kinnitatud nimekirjast'], ['Mõjutatav ökosüsteem', 'ELME2 tüüp'], ['Mõjutatav loodushüve või ökosüsteemiteenus', 'CICES v5.1'], ['Mõju suund ja tugevus', 'tõendusbaasist'], ['Ajaline avaldumine', 'lühi-, kesk-, pikaajaline'], ['Biofüüsikaline näitaja', 'stsenaariumi kalkulaatorist'], ['Rahaline väärtus', 'ainult kui metoodiliselt põhjendatav'], ['Kasutatavus otseses kulu-kasu võrdluses', 'teenuse kaupa ettepanek'], ['Kasutatud meetod ja andmeallikas', 'kihi id ja meetod'], ['Topeltarvestuse risk', 'teenuse kaupa ettepanek'], ['Ebakindlus', 'teenuse kaupa lipud'], ['Märkus sotsiaalmajandusliku mõju hindajale', 'teenuse kaupa']]) { const li = h('li', {}, ul); h('b', {}, li, n); h('span', {}, li, ` – ${d}`); }
  }
