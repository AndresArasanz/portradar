# PortRadar

Radar de ports nativos no oficiales de PS4 a PC publicados en GitHub: estado,
última versión, estrellas, actividad y lo que dice cada autor, actualizado a
diario sin IA.

- **Web:** https://ports.ibaietarra.com (GitHub Pages)
- **Ficha (alcance y criterios):** [`FICHA.md`](FICHA.md)
- **Decisiones:** [`docs/decisions/`](docs/decisions/)
- **Historial:** [`CHANGELOG.md`](CHANGELOG.md)

## Cómo funciona

| Pieza | Qué hace |
|---|---|
| `data/ports.json` | Lista curada a mano: juego, repo, sistema, estado (`play`/`alpha`/`early`), hasta dónde llega y nota |
| `data/github.json` | Datos automáticos de cada repo (estrellas, release, último push, fork, Status del README…) |
| `data/candidates.json` | Repos nuevos encontrados por la búsqueda diaria, pendientes de revisar |
| `data/follows.json` | Juegos que sigo (los cambia la web) |
| `data/review.json` | Repos descartados (los cambia la web) |
| `collector/` | Recolector en Python sin dependencias; lo ejecuta cada día `.github/workflows/update.yml` |
| `web/` | Web estática; `scripts/build_site.sh` la monta junto con `data/` |

## Seguir juegos y revisar repos nuevos desde la web

La web guarda esos cambios haciendo commits en este repo. Necesita un token
*fine-grained* que se pega una vez en cada navegador (botón **Conectar**):

1. GitHub → Settings → Developer settings → [Fine-grained tokens → Generate new token](https://github.com/settings/personal-access-tokens/new)
2. **Repository access:** *Only select repositories* → `AndresArasanz/portradar`
3. **Permissions → Repository → Contents:** *Read and write* (nada más)
4. Caducidad: la que quieras (al caducar, la web vuelve a modo solo lectura)

El token se guarda solo en ese navegador (`localStorage`); nunca va al repo.
Si se filtra, solo permite tocar este repo público y se revoca en un clic.

## Editar estado, "hasta dónde llega" o notas

Son campos manuales: editar `data/ports.json` (en GitHub o en local) y hacer
commit. La CI valida el fichero; un repo aceptado desde la web entra con estado
`early` y sin sistema, para completarlo así.

## Desarrollo local

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python -m pytest --cov=collector     # recolector + validación + E2E
npm test                                         # lógica de la web (node --test)
GITHUB_TOKEN=$(gh auth token) .venv/bin/python -m collector.main data   # actualizar a mano
scripts/build_site.sh && python3 -m http.server -d _site 8000          # ver la web
```
