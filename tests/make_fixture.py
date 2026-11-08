"""Génère le projet PBIP synthétique « CAS_LIMITES » utilisé par les tests.

Usage : python3 make_fixture.py <dossier_de_sortie>
Produit trois variantes :
  CAS_LIMITES/          PBIP complet, rapport au format PBIR (dossier definition/pages)
  CAS_LIMITES_LEGACY/   même modèle, rapport au format PBIR-Legacy (report.json)
  CAS_BIM/              modèle enregistré en model.bim (TMSL), sans TMDL
Toutes les valeurs sont fictives.
"""
import json, os, sys, shutil

OUT = sys.argv[1]
T = '\t'

def w(path, txt):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(txt)

def tm(*lines):
    return '\n'.join(lines) + '\n'

MODEL = tm(
    'model Model',
    '\tculture: fr-FR',
    '\tdefaultPowerBIDataSourceVersion: powerBI_V3',
    '\tsourceQueryCulture: fr-FR',
    '',
    'ref table Ventes',
)

DATABASE = tm('database', '\tcompatibilityLevel: 1601')

EXPRESSIONS = tm(
    '/// URL de base de l\'API de démonstration',
    'expression UrlApi = "https://api.exemple.org/v1" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
    '\tlineageTag: 11111111-0000-0000-0000-000000000001',
    '\tqueryGroup: Paramètres',
    '',
    '\tannotation PBI_ResultType = Text',
    '',
    '/// Requête partagée lue par la table Referentiel',
    'expression RequetePartagee =',
    '\t\tlet',
    '\t\t    Source = Json.Document(Web.Contents(UrlApi, [RelativePath = "referentiel"])),',
    '\t\t    Tableau = Table.FromRecords(Source)',
    '\t\tin',
    '\t\t    Tableau',
    '\tlineageTag: 11111111-0000-0000-0000-000000000002',
    '',
    '\tannotation PBI_ResultType = Table',
)

def col(name, dtype, src=None, extra=()):
    lines = [f'\tcolumn {name}', f'\t\tdataType: {dtype}', f'\t\tlineageTag: 0', f'\t\tsummarizeBy: none']
    if src:
        lines.append(f'\t\tsourceColumn: {src}')
    lines += list(extra)
    lines.append('')
    return lines

def mpart(name, code_lines, mode='import'):
    return [f'\tpartition {name} = m', f'\t\tmode: {mode}', '\t\tsource =',
            *['\t\t\t\t' + l for l in code_lines], '']

TABLES = {}

TABLES['Ventes'] = tm(
    'table Ventes',
    '\tlineageTag: 0',
    '',
    '\tmeasure \'Total ventes\' = SUM(Ventes[Montant])',
    '\t\tformatString: #,##0',
    '\t\tlineageTag: 0',
    '',
    '\t/// Ventes de la même période l\'année précédente',
    '\tmeasure \'Ventes N-1\' =',
    '\t\t\tCALCULATE (',
    '\t\t\t\t[Total ventes],',
    '\t\t\t\tSAMEPERIODLASTYEAR ( \'Calendrier\'[Date] )',
    '\t\t\t)',
    '\t\tformatString: #,##0',
    '\t\tlineageTag: 0',
    '',
    '\tmeasure \'Mesure piège\' = ```',
    '\t\t\t// [Fantôme] et Produits[Inexistante] sont dans un commentaire',
    '\t\t\tVAR txt = "[Total ventes] dans une chaîne"',
    '\t\t\tRETURN',
    '\t\t\t\tSUMX ( ventes, ventes[montant] ) + [ventes n-1]',
    '\t\t\t```',
    '\t\tlineageTag: 0',
    '',
    '\tmeasure \'Photo produit\' = "https://exemple.org/photo.png"',
    '\t\tdataCategory: ImageUrl',
    '\t\tlineageTag: 0',
    '',
    *col('DateVente', 'dateTime', 'DateVente'),
    *col('ProduitKey', 'int64', 'ProduitKey'),
    *col('RegionKey', 'int64', 'RegionKey'),
    *col('Montant', 'decimal', 'Montant'),
    *mpart('Ventes', [
        'let',
        '    Source = Csv.Document(File.Contents("C:\\Donnees\\ventes.csv"), [Delimiter=";", Encoding=65001]),',
        '    Entetes = Table.PromoteHeaders(Source)',
        'in',
        '    Entetes']),
)

TABLES['Produits'] = tm(
    'table Produits',
    '\tlineageTag: 0',
    '',
    *col('ProduitKey', 'int64', 'ProduitKey', ['\t\tisKey']),
    *col('Libellé', 'string', 'Libelle'),
    *mpart('Produits', [
        'let',
        '    Source = Sql.Database("srv-sql.exemple.local", "Ventes"),',
        '    dbo_Produits = Source{[Schema="dbo",Item="Produits"]}[Data]',
        'in',
        '    dbo_Produits']),
)

TABLES['Region'] = tm(
    "table 'Région d''Europe'",
    '\tlineageTag: 0',
    '',
    *col('RegionKey', 'int64', 'RegionKey'),
    *col('Zone', 'string', 'Zone'),
    *mpart("'Région d''Europe'", [
        'let',
        '    Source = Folder.Files("C:\\Donnees\\Regions"),',
        '    Premier = Source{0}[Content]',
        'in',
        '    Premier']),
)

TABLES['Calendrier'] = tm(
    'table Calendrier',
    '\tlineageTag: 0',
    '\tdataCategory: Time',
    '',
    *col('Date', 'dateTime', 'Date', ['\t\tisKey']),
    *col('Année', 'int64', 'Annee'),
    *mpart('Calendrier', [
        'let',
        '    Dates = List.Dates(#date(2024,1,1), 731, #duration(1,0,0,0)),',
        '    Table = Table.FromList(Dates, Splitter.SplitByNothing(), {"Date"})',
        'in',
        '    Table']),
)

TABLES['Analytics'] = tm(
    'table Analytics',
    '\tlineageTag: 0',
    '',
    *col('Visites', 'int64', 'Visites'),
    *mpart('Analytics', [
        'let',
        '    Source = GoogleAnalytics.Accounts(),',
        '    Compte = Source{0}[Data]',
        'in',
        '    Compte']),
)

TABLES['Referentiel'] = tm(
    'table Referentiel',
    '\tlineageTag: 0',
    '',
    *col('Code', 'string', 'Code'),
    *mpart('Referentiel', [
        'let',
        '    Source = RequetePartagee',
        'in',
        '    Source']),
)

TABLES['CalculTemps'] = tm(
    "table 'Calcul temps'",
    '\tlineageTag: 0',
    '',
    '\tcalculationGroup',
    '\t\tprecedence: 1',
    '',
    "\t\tcalculationItem 'Période courante' = SELECTEDMEASURE()",
    '',
    '\t\tcalculationItem CumulAnnuel =',
    "\t\t\t\tCALCULATE ( SELECTEDMEASURE (), DATESYTD ( 'Calendrier'[Date] ) )",
    '',
    "\t\tcalculationItem 'Écart N-1' = ```",
    '\t\t\t\tVAR n1 = CALCULATE ( SELECTEDMEASURE (), SAMEPERIODLASTYEAR ( \'Calendrier\'[Date] ) )',
    '\t\t\t\tRETURN SELECTEDMEASURE () - n1',
    '\t\t\t\t```',
    '\t\t\tformatStringDefinition = SELECTEDMEASUREFORMATSTRING()',
    '',
    *col("'Calcul temps'", 'string', 'Name', ['\t\tsortByColumn: Ordinal']),
    *col('Ordinal', 'int64', 'Ordinal', ['\t\tisHidden']),
    "\tpartition 'Calcul temps' = calculationGroup",
    '\t\tmode: import',
    '',
)

TABLES['ChoixIndicateur'] = tm(
    "table 'Choix indicateur'",
    '\tlineageTag: 0',
    '',
    *col("'Choix indicateur'", 'string', '[Value1]', ["\t\tsortByColumn: 'Choix indicateur Ordre'"]),
    "\tcolumn 'Choix indicateur Champs'",
    '\t\tdataType: string',
    '\t\tisHidden',
    '\t\tlineageTag: 0',
    '\t\tsummarizeBy: none',
    '\t\tsourceColumn: [Value2]',
    '',
    '\t\textendedProperty ParameterMetadata =',
    '\t\t\t\t{',
    '\t\t\t\t  "version": 3,',
    '\t\t\t\t  "kind": 2',
    '\t\t\t\t}',
    '',
    *col("'Choix indicateur Ordre'", 'int64', '[Value3]', ['\t\tisHidden']),
    "\tpartition 'Choix indicateur' = calculated",
    '\t\tmode: import',
    '\t\tsource =',
    '\t\t\t\t{',
    "\t\t\t\t    (\"Total ventes\", NAMEOF('Ventes'[Total ventes]), 0),",
    "\t\t\t\t    (\"Ventes N-1\", NAMEOF('Ventes'[Ventes N-1]), 1)",
    '\t\t\t\t}',
    '',
)

TABLES['_Mesures'] = tm(
    'table _Mesures',
    '\tlineageTag: 0',
    '',
    '\tmeasure \'Utilisateur connecté\' = USERPRINCIPALNAME()',
    '\t\tlineageTag: 0',
    '',
    '\tmeasure \'Part des ventes\' = DIVIDE([Total ventes], CALCULATE([Total ventes], ALL(\'Région d\'\'Europe\')))',
    '\t\tformatString: 0.0%',
    '\t\tlineageTag: 0',
    '',
    *mpart('_Mesures', [
        'let',
        '    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("i44FAA==", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [Colonne1 = _t])',
        'in',
        '    Source']),
)

RELATIONSHIPS = tm(
    'relationship a1',
    '\tfromColumn: Ventes.ProduitKey',
    '\ttoColumn: Produits.ProduitKey',
    '',
    'relationship a2',
    '\tcrossFilteringBehavior: bothDirections',
    '\tfromColumn: Ventes.RegionKey',
    "\ttoColumn: 'Région d''Europe'.RegionKey",
    '',
    'relationship a3',
    '\tfromColumn: Ventes.DateVente',
    '\ttoColumn: Calendrier.Date',
    '',
    'relationship a4',
    '\tisActive: false',
    '\tfromColumn: Ventes.DateVente',
    '\ttoColumn: Calendrier.Année',
)

ROLES = {
    'Lecteur Est': tm(
        "role 'Lecteur Est'",
        '\tmodelPermission: read',
        '',
        '\tmember utilisateur.fictif@exemple.org',
        '',
        "\ttablePermission 'Région d''Europe' = [Zone] = \"Est\"",
    ),
    'Responsable': tm(
        'role Responsable',
        '\tmodelPermission: read',
        '',
        '\ttablePermission Produits =',
        '\t\t\tVAR u = USERPRINCIPALNAME ()',
        '\t\t\tRETURN',
        '\t\t\t\tNOT ISBLANK ( u )',
        '',
        '\tannotation PBI_Id = 0',
    ),
    'Administrateur': tm(
        'role Administrateur',
        '\tmodelPermission: read',
    ),
}

def semantic_model(base, name):
    sm = os.path.join(base, f'{name}.SemanticModel')
    d = os.path.join(sm, 'definition')
    w(os.path.join(sm, 'definition.pbism'), json.dumps({'version': '4.2', 'settings': {}}, indent=2))
    w(os.path.join(d, 'model.tmdl'), MODEL)
    w(os.path.join(d, 'database.tmdl'), DATABASE)
    w(os.path.join(d, 'expressions.tmdl'), EXPRESSIONS)
    w(os.path.join(d, 'relationships.tmdl'), RELATIONSHIPS)
    for fn, txt in TABLES.items():
        w(os.path.join(d, 'tables', fn + '.tmdl'), txt)
    for fn, txt in ROLES.items():
        w(os.path.join(d, 'roles', fn + '.tmdl'), txt)

def visual(name, vtype, prop, x=0):
    return {'name': name, 'position': {'x': x, 'y': 0, 'width': 300, 'height': 200},
            'visual': {'visualType': vtype, 'query': {'queryState': {'Values': {'projections': [
                {'field': {'Measure': {'Expression': {'SourceRef': {'Entity': 'Ventes'}}, 'Property': prop}},
                 'queryRef': 'Ventes.' + prop}]}}}}}

# Ordre voulu : Accueil, Détail (masquée), Synthèse. Les identifiants de dossier sont
# volontairement dans un autre ordre alphabétique pour vérifier la lecture de pages.json.
PAGES = [('zz_accueil', 'Accueil', False, [visual('v1', 'card', 'Total ventes')]),
         ('aa_detail', 'Détail', True, [visual('v2', 'tableEx', 'Ventes N-1'), visual('v3', 'slicer', 'Zone')]),
         ('mm_synthese', 'Synthèse', False, [])]

def report_pbir(base, name):
    r = os.path.join(base, f'{name}.Report')
    w(os.path.join(r, 'definition.pbir'), json.dumps({'version': '4.0', 'datasetReference': {'byPath': {'path': f'../{name}.SemanticModel'}}}, indent=2))
    d = os.path.join(r, 'definition')
    w(os.path.join(d, 'report.json'), json.dumps({'themeCollection': {}}, indent=2))
    w(os.path.join(d, 'pages', 'pages.json'), json.dumps({'pageOrder': [p[0] for p in PAGES], 'activePageName': PAGES[0][0]}, indent=2))
    for pid, disp, hidden, vis in PAGES:
        pg = {'name': pid, 'displayName': disp, 'displayOption': 'FitToPage', 'height': 720, 'width': 1280}
        if hidden:
            pg['visibility'] = 'HiddenInViewMode'
        w(os.path.join(d, 'pages', pid, 'page.json'), json.dumps(pg, indent=2, ensure_ascii=False))
        for v in vis:
            w(os.path.join(d, 'pages', pid, 'visuals', v['name'], 'visual.json'), json.dumps(v, indent=2, ensure_ascii=False))

def report_legacy(base, name):
    r = os.path.join(base, f'{name}.Report')
    w(os.path.join(r, 'definition.pbir'), json.dumps({'version': '1.0', 'datasetReference': {'byPath': {'path': f'../{name}.SemanticModel'}}}, indent=2))
    sections = []
    for i, (pid, disp, hidden, vis) in enumerate(PAGES):
        cfg = {'visibility': 1} if hidden else {}
        sections.append({'name': pid, 'displayName': disp, 'ordinal': i, 'config': json.dumps(cfg),
                         'visualContainers': [{'x': 0, 'y': 0, 'width': 300, 'height': 200,
                                               'config': json.dumps({'name': v['name'], 'singleVisual': {'visualType': v['visual']['visualType'],
                                                   'projections': {'Values': [{'queryRef': 'Ventes.' + v['visual']['query']['queryState']['Values']['projections'][0]['field']['Measure']['Property']}]}}}, ensure_ascii=False)}
                                              for v in vis]})
    w(os.path.join(r, 'report.json'), json.dumps({'config': '{}', 'sections': sections}, indent=2, ensure_ascii=False))

if os.path.exists(OUT):
    shutil.rmtree(OUT)

base = os.path.join(OUT, 'CAS_LIMITES')
semantic_model(base, 'CAS_LIMITES'); report_pbir(base, 'CAS_LIMITES')
w(os.path.join(base, 'CAS_LIMITES.pbip'), json.dumps({'version': '1.0', 'artifacts': [{'report': {'path': 'CAS_LIMITES.Report'}}]}, indent=2))

base = os.path.join(OUT, 'CAS_LIMITES_LEGACY')
semantic_model(base, 'CAS_LIMITES_LEGACY'); report_legacy(base, 'CAS_LIMITES_LEGACY')

base = os.path.join(OUT, 'CAS_BIM')
w(os.path.join(base, 'CAS_BIM.SemanticModel', 'model.bim'), json.dumps({'name': 'x', 'model': {'tables': []}}, indent=2))
w(os.path.join(base, 'CAS_BIM.Report', 'definition.pbir'), '{}')
print('ok', OUT)
