# ADR-002 — Actualización diaria con GitHub Actions

**Fecha:** 2026-10-18 | **Estado:** Activo

## Decisión

Un workflow programado (cron diario) ejecuta el recolector en Python, que consulta la API
de GitHub con el `GITHUB_TOKEN` automático del workflow y hace commit de `data/` solo si
hay cambios.

## Alternativas descartadas

- Cron en el miniserver: exigiría un token propio guardado en el servidor y un push desde
  casa; con la web en Pages, el sitio natural es Actions.

## Por qué

No hay que crear ni guardar ningún token para la actualización, y GitHub ejecuta el job
aunque el miniserver esté apagado. Los commits diarios mantienen el repo activo, así que
GitHub no desactiva el workflow programado (lo hace tras 60 días sin actividad).
