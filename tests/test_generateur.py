"""Tests de non-régression du générateur de documentation PBIP.

Le script fabrique trois projets PBIP fictifs (make_fixture.py), les dépose dans le
générateur ouvert dans Chromium sans interface, puis compare le résultat à ce qui est
attendu. Aucun appel réseau n'est autorisé pendant le test.

Prérequis (une fois) :
    pip install playwright
    playwright install chromium

Lancer depuis la racine du dépôt :
    python tests/test_generateur.py
"""
import asyncio, os, shutil, subprocess, sys, tempfile, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.environ.get('PBIP_TOOL') or os.path.join(ROOT, 'generateur_documentation_francais.html')

try:
    from playwright.async_api import async_playwright
except ImportError:
    sys.exit('Playwright manquant : pip install playwright && playwright install chromium')

DUMP = r"""() => {
  const M = G.model;
  return {
    tables: Object.fromEntries(M.tables.map(t => [t.name, {type: t.type, src: t.srcType.kind, dc: t.dataCategory,
              cols: t.columns.length, meas: t.measures.length,
              cg: (t.calcGroup || []).map(i => [i.name, i.expression])}])),
    rels: M.relationships.length,
    roles: M.roles.map(r => [r.name, r.tablePerms.map(p => p.table)]),
    reach: M.roles.flatMap(r => r.tablePerms.map(p => [p.table, rlsReach(M, p.table)])),
    pages: M.pages.map(p => [p.name, p.hidden, p.visuals]),
    integrity: M.integrity.filter(c => !c.ok).map(c => c.label),
    conns: (M.connections || []).map(c => [c.kind, c.server, c.tables]),
    format: M.reportFormat,
  };
}"""

DEPS = r"""() => {
  [...document.querySelectorAll('.nav-btn')].find(b => b.textContent.startsWith('Dépendances'))?.click();
  const p = document.getElementById('panel-dependencies');
  return p ? p.innerText : '';
}"""

failures = []
def check(label, cond, detail=''):
    print(('  ok    ' if cond else '  ÉCHEC ') + label + ('' if cond else '  → ' + str(detail)))
    if not cond:
        failures.append(label)

def zip_dir(src, dst):
    with zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(src):
            for f in files:
                p = os.path.join(base, f)
                z.write(p, os.path.relpath(p, os.path.dirname(src)))

async def load(browser, zpath):
    page = await browser.new_page()
    errors, network = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('request', lambda r: network.append(r.url) if not r.url.startswith(('file:', 'data:', 'blob:')) else None)
    await page.goto('file://' + TOOL)
    await page.set_input_files('#fileIn', zpath)
    await page.click('#genBtn')
    try:
        await page.wait_for_selector('#app.on', timeout=20000)
        ok = True
    except Exception:
        ok = False
    return page, ok, errors, network

async def main():
    tmp = tempfile.mkdtemp(prefix='pbip_test_')
    try:
        subprocess.run([sys.executable, os.path.join(ROOT, 'tests', 'make_fixture.py'), tmp], check=True, capture_output=True)
        zips = {}
        for name in ('CAS_LIMITES', 'CAS_LIMITES_LEGACY', 'CAS_BIM'):
            zips[name] = os.path.join(tmp, name + '.zip')
            zip_dir(os.path.join(tmp, name), zips[name])

        async with async_playwright() as p:
            browser = await p.chromium.launch()

            print('CAS_LIMITES (rapport PBIR)')
            page, ok, errors, network = await load(browser, zips['CAS_LIMITES'])
            check('documentation générée', ok)
            d = await page.evaluate(DUMP)
            t = d['tables']
            check('9 tables', len(t) == 9, len(t))
            check('17 colonnes, 6 mesures', sum(x['cols'] for x in t.values()) == 17 and sum(x['meas'] for x in t.values()) == 6)
            check('4 relations', d['rels'] == 4, d['rels'])
            check('contrôle d\'intégrité sans écart', not d['integrity'], d['integrity'])
            check('ordre des pages lu dans pages.json', [x[0] for x in d['pages']] == ['Accueil', 'Détail', 'Synthèse'], d['pages'])
            check('page masquée repérée', d['pages'][1][1] is True)
            check('groupe de calcul : 3 éléments nommés', [i[0] for i in t['Calcul temps']['cg']] == ['Période courante', 'CumulAnnuel', 'Écart N-1'], t['Calcul temps']['cg'])
            check('groupe de calcul : expressions lues', all(i[1] for i in t['Calcul temps']['cg']))
            check('paramètre de champ détecté', t['Choix indicateur']['type'] == 'FieldParameter')
            check('catégorie d\'une mesure non attribuée à sa table', t['Ventes']['dc'] == '', t['Ventes']['dc'])
            check('table de dates (dataCategory de la table)', t['Calendrier']['type'] == 'DateDimension')
            expected_src = {'Ventes': 'csv', 'Produits': 'sql', "Région d'Europe": 'folder', 'Calendrier': 'generated',
                            'Analytics': 'unknown', 'Referentiel': 'web', '_Mesures': 'embedded',
                            'Calcul temps': 'calcgroup', 'Choix indicateur': 'calculated'}
            got_src = {k: v['src'] for k, v in t.items()}
            check('type de source de chaque table', got_src == expected_src, {k: (got_src.get(k), v) for k, v in expected_src.items() if got_src.get(k) != v})
            kinds = sorted(c[0] for c in d['conns'])
            check('connexions : aucune oubliée, inconnue signalée', kinds == ['csv', 'folder', 'sql', 'unknown', 'web'], kinds)
            check('requête partagée suivie jusqu\'à son URL', any(c[0] == 'web' and c[1] == 'https://api.exemple.org/v1' for c in d['conns']))
            check('rôles et tables filtrées (apostrophe conservée)', sorted(d['roles']) == sorted([['Administrateur', []], ['Responsable', ['Produits']], ['Lecteur Est', ["Région d'Europe"]]]), d['roles'])
            check('propagation RLS', sorted(map(tuple, [(a, tuple(b)) for a, b in d['reach']])) == [('Produits', ('Ventes',)), ("Région d'Europe", ('Ventes',))], d['reach'])
            deps = await page.evaluate(DEPS)
            check('dépendances : commentaire et chaîne ignorés', 'Fantôme' not in deps and 'Inexistante' not in deps)
            check('dépendances : majuscules indifférentes', 'Ventes[Montant]' in deps and 'Ventes N-1' in deps)
            html = await page.content()
            check('membres de rôle jamais affichés', 'utilisateur.fictif@exemple.org' not in html)
            check('aucune erreur JavaScript', not errors, errors)
            check('aucun appel réseau', not network, network)
            await page.close()

            print('CAS_LIMITES_LEGACY (rapport PBIR-Legacy)')
            page, ok, errors, network = await load(browser, zips['CAS_LIMITES_LEGACY'])
            d = await page.evaluate(DUMP)
            check('format PBIR-Legacy reconnu', d['format'] == 'PBIR-Legacy', d['format'])
            check('pages lues dans report.json', [x[:2] for x in d['pages']] == [['Accueil', False], ['Détail', True], ['Synthèse', False]], d['pages'])
            check('aucune erreur JavaScript', not errors, errors)
            await page.close()

            print('CAS_BIM (modèle au format model.bim)')
            page, ok, errors, network = await load(browser, zips['CAS_BIM'])
            msg = await page.inner_text('#errMsg')
            check('message d\'erreur explicite', (not ok) and 'model.bim' in msg, msg)
            await page.close()
            await browser.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        print(f'{len(failures)} test(s) en échec.')
        sys.exit(1)
    print('Tous les tests sont passés.')

asyncio.run(main())
