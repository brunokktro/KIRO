#!/usr/bin/env bash
# Gera a copia de EXECUCAO de um fixture, sem gabarito.
#
# O fixture autorado carrega comentarios de desenho de teste (qual construto foi plantado,
# qual questao ele exercita, o que o run tem que reportar). Se essa copia for analisada, o
# agente LE o gabarito e devolve ele: o teste nao prova nada.
#
# Este script produz uma copia realista: remove os arquivos de spec e todo comentario de
# meta-teste, e ASSERTA que nenhuma referencia a question id sobrou. Falha se sobrar.
#
#   ./make-run-copy.sh <fixture-dir> <dest-dir>
set -euo pipefail

SRC="${1:?uso: make-run-copy.sh <fixture-dir> <dest-dir>}"
DEST="${2:?uso: make-run-copy.sh <fixture-dir> <dest-dir>}"

rm -rf "$DEST"; mkdir -p "$DEST"
cp -R "$SRC"/. "$DEST"/
rm -rf "$DEST/.git"
# arquivos que SAO o gabarito
rm -f "$DEST/EXPECTED-FINDINGS.md" "$DEST/README.md" "$DEST/make-run-copy.sh"

python3 - "$DEST" <<'PY'
import re, sys, os

dest = sys.argv[1]
# marcadores de comentario de meta-teste. Comentario que casa qualquer um destes sai.
LEAK = re.compile(
    r'PLANTED|BUCKET \d|CONTROL RESOURCE|fixture|rubric|must not flag|'
    r'(?:APP|INF|SEC|OPS|DATA)-Q\d+|deliberately|seeded|a run that|'
    r'has failed|has under-answered|no EKS equivalent|no equivalent|'
    r'hard fail|false positive|proves the app|do not collapse|'
    r'Portable:|OpenShift-only:|escalates|de-escalates',
    re.I)

TEXT_EXT = {'.yaml', '.yml', '.sh', '.md', ''}
removed = 0
for root, _, files in os.walk(dest):
    if '.git' in root:
        continue
    for name in files:
        p = os.path.join(root, name)
        ext = os.path.splitext(name)[1]
        if ext not in TEXT_EXT and name != 'Dockerfile':
            continue
        try:
            lines = open(p, encoding='utf-8').read().split('\n')
        except (UnicodeDecodeError, OSError):
            continue
        out = []
        for i, l in enumerate(lines):
            s = l.strip()
            is_comment = s.startswith('#') and not s.startswith('#!')
            if is_comment and LEAK.search(s):
                removed += 1
                continue
            out.append(l)
        txt = re.sub(r'\n{3,}', '\n\n', '\n'.join(out))
        # nao deixar comentario orfao vazio no topo
        txt = re.sub(r'^(#!/[^\n]*\n)#\n', r'\1', txt)
        txt = re.sub(r'\A#\n', '', txt)
        open(p, 'w', encoding='utf-8').write(txt)
print(f"comentarios de gabarito removidos: {removed}")
PY

echo "=== assercao: zero referencia a question id ou meta-teste ==="
if grep -rniE '(APP|INF|SEC|OPS|DATA)-Q[0-9]+|PLANTED|EXPECTED-FINDINGS' "$DEST" \
     --exclude-dir=.git 2>/dev/null; then
  echo "FALHOU: gabarito vazou para a copia de execucao"
  exit 1
fi
echo "  LIMPO"

echo "=== assercao: YAML ainda parseia ==="
python3 - "$DEST" <<'PY'
import yaml, glob, sys, os
dest = sys.argv[1]
total = 0
for f in sorted(glob.glob(os.path.join(dest, 'manifests', '*.yaml'))):
    docs = [d for d in yaml.safe_load_all(open(f)) if d]
    total += len(docs)
    print(f"  OK {os.path.basename(f):32} {len(docs)} docs")
print(f"  total {total} documentos")
if total == 0:
    sys.exit("FALHOU: nenhum documento YAML")
PY

cd "$DEST"
git init -q
git -c user.email=fixture@local -c user.name=fixture add -A
git -c user.email=fixture@local -c user.name=fixture commit -q -m "baseline: fixture run copy"
echo "=== baseline git: $(git rev-parse --short HEAD) ($(git ls-files | wc -l | tr -d ' ') arquivos) ==="
