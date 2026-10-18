# portradar — instrucciones para Claude Code

Radar de ports nativos no oficiales de PS4 a PC publicados en GitHub: estado, última versión, estrellas y actividad, actualizado a diario sin IA.

Este proyecto sigue el método del miniserver: `/home/miniserver/docs/metodo/METODO.md`.

## Reglas del proyecto

- No implementar nada que no esté en `FICHA.md` (o en una ficha nueva aprobada). Lo que esté en "Fuera de alcance" no se toca.
- Decisiones no obvias → nuevo ADR en `docs/decisions/` (copiar `ADR-000-plantilla.md`).
- Secretos solo en `.env` (nunca en git); mantener `.env.example` con las claves vacías.
- Antes de dar algo por terminado, cumplir la checklist "Terminado" de `FICHA.md`.

## Contexto

- Web estática en GitHub Pages (`ports.ibaietarra.com`, CNAME **sin proxy** de Cloudflare por el MITM de DIGI). No hay backend ni puerto en el miniserver.
- Datos en `data/*.json`: `ports.json` manual; `github.json`/`candidates.json` los escribe el recolector; `follows.json`/`review.json` los escribe la web vía API de contenidos con el token del usuario.
- Estado Jugable/Alfa/Temprano y "hasta dónde llega" son manuales: no calcularlos ni inventar porcentajes.
- Ser fork NO es señal de peligro (Bloodborne Windows, GoW3 y GT Sport son forks): etiqueta neutra "fork de X".
- Tests: `.venv/bin/python -m pytest` (incluye E2E Playwright) y `npm test` (node, nvm en ~/.nvm).
- El workflow diario hace commits en `main`: hacer siempre `git pull --rebase` antes de `git push` desde el miniserver.
