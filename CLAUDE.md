# portradar — instrucciones para Claude Code

Radar de ports nativos no oficiales de PS4 a PC publicados en GitHub: estado, última versión, estrellas y actividad, actualizado a diario sin IA.

Este proyecto sigue el método del miniserver: `/home/miniserver/docs/metodo/METODO.md`.

## Reglas del proyecto

- No implementar nada que no esté en `FICHA.md` (o en una ficha nueva aprobada). Lo que esté en "Fuera de alcance" no se toca.
- Decisiones no obvias → nuevo ADR en `docs/decisions/` (copiar `ADR-000-plantilla.md`).
- Secretos solo en `.env` (nunca en git); mantener `.env.example` con las claves vacías.
- Antes de dar algo por terminado, cumplir la checklist "Terminado" de `FICHA.md`.

## Contexto

<!-- rutas, puertos, servicios externos, cosas que un agente nuevo debe saber -->
