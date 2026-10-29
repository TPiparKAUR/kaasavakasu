  /* ---------- Metoodika võrdlus (v1 → v2) ---------- */
  const V1_URL = 'https://tpiparkaur.github.io/kaasavakasu/';
  const share = (x, d = 0) => (x === null || x === undefined || !Number.isFinite(x) ? '–' : `${nf(d).format(x * 100)} %`);
  const medianOf = (xs) => { const v = xs.filter((x) => Number.isFinite(x)).sort((a, b) => a - b); if (!v.length) return null; const m = v.length >> 1; return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2; };
  function compareView(root) {
    const V = D.V;
    if (!V) { h('p', { class: 'empty' }, root, 'Võrdluse andmed puuduvad (käivita scripts/vordle_metoodikad.py).'); return; }
    if (!S.cmp) S.cmp = { level: 'okosusteem' };
    const rows = V.kihid.map((r) => Object.fromEntries(V.kihid_veerud.map((c, i) => [c, r[i]])));
    const card = h('section', { class: 'card' }, root);
    h('h2', {}, card, 'Metoodika võrdlus: vana (v1) ja uus (v2)');
    h('p', { class: 'sub' }, card, 'Vana arvutus (v1) kasutas aritmeetilist keskmist ja jättis pikslid, kus kihil väärtus puudub (NoData), arvutusest välja. Uus arvutus (v2) kasutab mediaani ja loeb need pikslid nulliks, välja arvatud erandkihid. Erinevus on jagatud kaheks: mis muutus valimis (millised pikslid arvutusse lähevad) ja mis muutus statistikus (keskmine või mediaan).');
    const act = h('div', { class: 'tools' }, card);
    h('a', { class: 'btn ghostbtn', href: V1_URL, target: '_blank', rel: 'noopener' }, act, 'Ava vana leht (v1)');
    const tot = V.muutus.okosusteem.kokku, n = (k) => tot[k] || 0;
    const ul = h('ul', { class: 'cols' }, card);
    for (const [k, t] of [['jäi oluliseks, sama suund', 'järeldust ei muutnud'], ['ei ole enam oluline', 'ei ole enam oluline'], ['muutus oluliseks', 'muutus oluliseks'], ['suund muutus', 'muutis suunda'], ['hinnang lisandus', 'on uued (v1-s polnud piisavalt andmeid)']]) { const li = h('li', {}, ul); h('b', {}, li, String(n(k))); h('span', {}, li, ` ökosüsteemi tasandi hinnangut ${t}`); }

    // 1. valimireeglid
    const c1 = h('section', { class: 'card' }, root);
    h('h2', {}, c1, '1. Mis muutus valimis');
    h('p', { class: 'sub' }, c1, 'Siin on statistik mõlemal pool sama (keskmine), muutunud on ainult pikslite valik. „Kaetud pindala“ näitab, kui suur osa klasside pindalast on arvutuses. Tüüpiline muutus on kihi tüübi × seisundi keskmiste suhtelise muutuse mediaan.');
    const by = new Map();
    for (const r of rows) { if (!by.has(r.pohjus)) by.set(r.pohjus, []); by.get(r.pohjus).push(r); }
    const t1 = h('table', { class: 'data' }, h('div', { class: 'scroll' }, c1)), hd1 = h('tr', {}, h('thead', {}, t1));
    for (const x of ['Põhjus', 'Kihte', 'Kaetud pindala v1 → v2', 'Keskmise tüüpiline muutus', 'Olulisi muutusi v1 → v2 (keskmine)']) h('th', {}, hd1, x);
    const tb1 = h('tbody', {}, t1);
    for (const [k, txt] of Object.entries(V.pohjused)) {
      const g = by.get(k); if (!g) continue;
      const sum = (c) => g.reduce((a, r) => a + (r[c] || 0), 0);
      const tr = h('tr', {}, tb1); h('td', {}, tr, txt); h('td', { class: 'num' }, tr, String(g.length));
      h('td', { class: 'num' }, tr, `${share(medianOf(g.map((r) => r.kate_v1)))} → ${share(medianOf(g.map((r) => r.kate_v2)))}`);
      h('td', { class: 'num' }, tr, share(medianOf(g.map((r) => r.abs_rel_valim_mediaan)), 1));
      h('td', { class: 'num' }, tr, `${sum('olulisi_v1')} → ${sum('olulisi_v2_keskmine')}`);
    }
    h('p', { class: 'note' }, c1, 'Kui NoData loetakse nulliks, kasvab kaetud pindala ja keskmine väheneb: pikslid, kus teenust ei ole, lähevad nüüd arvutusse nullina. Erandkihtides (§) jäeti NoData välja nagu v1-s, seega nende keskmine ei muutu. Madalama lahutusvõimega kihid (‡) arvutati v1-s ainult segumudeliga; v2-s viidi need 10 m lahutusvõimele.');

    // 2. statistik
    const c2 = h('section', { class: 'card' }, root);
    h('h2', {}, c2, '2. Mis muutus statistikus: keskmine → mediaan');
    h('p', { class: 'sub' }, c2, 'Siin on valim mõlemal pool sama (v2 reeglid), muutunud on ainult statistik. Mediaan näitab tüüpilist pikslit; keskmist tõstavad üksikud suured väärtused.');
    const L = V.lahtrid || {}, ul2 = h('ul', { class: 'cols' }, c2);
    h('span', {}, h('li', {}, ul2), `${share(L.osa_mediaan_vaiksem)} tüübi × seisundi lahtritest on mediaan keskmisest väiksem.`);
    h('span', {}, h('li', {}, ul2), `${share(L.osa_mediaan_null)} lahtritest on mediaan 0, kuigi keskmine on suurem kui 0: teenust on vähestes kohtades. Siis näitab tulemustabel ka mediaani kohtades, kus teenus esineb.`);
    h('p', { class: 'note' }, c2, 'Seetõttu on mediaanipõhiseid olulisi muutusi tavaliselt vähem kui keskmisepõhiseid: mediaan ei reageeri üksikutele suurtele väärtustele.');

    // 3. olulisuse muutus
    const c3 = h('section', { class: 'card' }, root);
    h('h2', {}, c3, '3. Kuidas muutusid järeldused');
    h('p', { class: 'sub' }, c3, 'Paaritatud hinnangute arv olulisuse muutuse kaupa (FDR q < 0,05).');
    const tools = h('div', { class: 'tools' }, c3); h('span', { class: 'tl' }, tools, 'Tase');
    const sg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Tase' }, tools);
    for (const [v, t] of [['okosusteem', 'ökosüsteem'], ['alam', 'alamökosüsteem']]) { const b = h('button', { type: 'button', 'aria-pressed': String(S.cmp.level === v) }, sg, t); b.onclick = () => { S.cmp.level = v; renderAll(true); }; }
    const M = V.muutus[S.cmp.level];
    const t3 = h('table', { class: 'data' }, h('div', { class: 'scroll' }, c3)), hd3 = h('tr', {}, h('thead', {}, t3));
    for (const x of ['', '1. Valim (v1 → v2, keskmine)', '2. Statistik (v2 keskmine → mediaan)', 'Kokku (v1 → v2)']) h('th', {}, hd3, x);
    const tb3 = h('tbody', {}, t3);
    for (const k of V.klassid) {
      if (!['valim', 'statistik', 'kokku'].some((p) => M[p][k])) continue;
      const tr = h('tr', {}, tb3); h('td', {}, tr, k);
      for (const p of ['valim', 'statistik', 'kokku']) h('td', { class: 'num' }, tr, String(M[p][k] || 0));
    }

    // 4. kihtide kaupa
    const c4 = h('section', { class: 'card' }, root);
    h('h2', {}, c4, 'Kihtide kaupa');
    const bar = h('div', { class: 'tools' }, c4);
    btn(bar, 'Laadi alla CSV (kihid)', 'ghost', () => saveText('vordlus_kihid.csv', [V.kihid_veerud.join(','), ...V.kihid.map((r) => r.map(csvQ).join(','))].join('\n')));
    if (!window.__OKS__) for (const f of ['lahtrid', 'paarid']) h('a', { class: 'btn ghostbtn', href: `data/vordlus_${f}.csv`, download: `vordlus_${f}.csv` }, bar, `CSV (${f})`);
    const det = h('details', {}, c4); h('summary', {}, det, `Näita tabelit (${rows.length} kihti)`);
    const t4 = h('table', { class: 'data' }, h('div', { class: 'scroll' }, det)), hd4 = h('tr', {}, h('thead', {}, t4));
    for (const x of ['Teenus', 'Põhjus', 'Kaetud v1', 'Kaetud v2', 'Keskmise muutus', 'Keskmine → mediaan', 'Olulisi v1', 'v2 keskmine', 'v2 mediaan', 'Suund muutus', 'Uued']) h('th', {}, hd4, x);
    const tb4 = h('tbody', {}, t4);
    for (const r of rows) {
      const tr = h('tr', {}, tb4); h('td', {}, tr, r.nimi); h('td', {}, tr, V.pohjused[r.pohjus]);
      for (const c of ['kate_v1', 'kate_v2', 'abs_rel_valim_mediaan', 'abs_rel_statistik_mediaan']) h('td', { class: 'num' }, tr, share(r[c], c.startsWith('abs') ? 1 : 0));
      for (const c of ['olulisi_v1', 'olulisi_v2_keskmine', 'olulisi_v2_mediaan', 'suund_muutus', 'hinnang_lisandus']) h('td', { class: 'num' }, tr, String(r[c] ?? '–'));
    }
    h('p', { class: 'note' }, c4, 'Keskmise muutus ja „keskmine → mediaan“ on kihi tüübi × seisundi lahtrite suhtelise erinevuse mediaan (absoluutväärtus). Olulisi = ökosüsteemi tasandi paaritatud hinnangud, q < 0,05.');
  }
