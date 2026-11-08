# Composants tiers

Le fichier `generateur_documentation_francais.html` embarque deux bibliothèques JavaScript, sans modification, et des règles adaptées d'un fichier publié par Microsoft. Chacun reste soumis à sa propre licence, reproduite ou référencée ci-dessous.

| Composant | Version | Usage dans l'outil | Licence |
|---|---|---|---|
| [JSZip](https://github.com/Stuk/jszip) | 3.10.1 | Lecture du ZIP dans le navigateur | MIT ou GPLv3, au choix (MIT retenue ici) |
| [pako](https://github.com/nodeca/pako), inclus dans JSZip | — | Décompression | MIT et Zlib |
| [ExcelJS](https://github.com/exceljs/exceljs) | build du 19/10/2023 | Export Excel | MIT |
| [BPARules.json](https://github.com/microsoft/Analysis-Services/tree/master/BestPracticeRules) | copie du 23/09/2026 | Règles de l'onglet Bonnes pratiques, traduites en français et réécrites en JavaScript | MIT |

L'en-tête de licence de JSZip est conservé dans le fichier HTML. Les deux bibliothèques ne sont pas recopiées dans les fichiers exportés.

---

## JSZip

```
Copyright (c) 2009-2016 Stuart Knightley, David Duponchel, Franz Buchinger, António Afonso

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```

Texte complet : <https://github.com/Stuk/jszip/blob/main/LICENSE.markdown>

## pako

```
Copyright (C) 2014-2017 by Vitaly Puzrin and Andrei Tuputcyn
```

Même texte de licence MIT que ci-dessus. Texte complet : <https://github.com/nodeca/pako/blob/main/LICENSE>

## ExcelJS

```
Copyright (c) 2014-2019 Guyon Roche
```

Même texte de licence MIT que ci-dessus. Texte complet : <https://github.com/exceljs/exceljs/blob/master/LICENSE>. Le paquet regroupe lui-même des dépendances publiées sous licences permissives (MIT, ISC, BSD) ; voir le dépôt ExcelJS pour le détail.

## BPARules.json (Microsoft Analysis Services)

```
Copyright (c) 2016 Microsoft
```

Même texte de licence MIT que ci-dessus. Texte complet : <https://github.com/microsoft/Analysis-Services/blob/master/LICENSE>

Les règles ont été traduites et réécrites pour fonctionner sur les fichiers TMDL, sans données. Chaque règle indique dans l'outil si sa logique est identique à la règle d'origine ou approchée.
