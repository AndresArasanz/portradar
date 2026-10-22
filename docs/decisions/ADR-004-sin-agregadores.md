# ADR-004 — No usar datos de agregadores de ports

**Fecha:** 2026-10-22 | **Estado:** Activo (issue #1)

## Decisión

PortRadar sigue sacando todo de la API de GitHub (búsquedas + vigilados). No se
rastrean ni se copian datos de PlayPorted, RecompHub, Duskport ni decomp.dev;
se pueden consultar a mano para añadir juegos a `ports.json` o `watch.json`.

## Alternativas descartadas

- Importar el catálogo de PlayPorted/RecompHub — no tienen API pública
  (PlayPorted prohíbe `/api/` en `robots.txt`); rastrear su HTML se rompe sin
  aviso y va contra lo que piden.

## Por qué

Esos catálogos ya dan la vista general, pero no tienen favoritos propios ni
avisan de juegos anunciados sin repo, que es lo que aporta PortRadar. Depender
solo de GitHub mantiene el recolector simple y estable; el coste es que lo que
no esté en GitHub hay que añadirlo a mano.
