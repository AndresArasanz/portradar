# ADR-003 — Favoritos y revisiones guardados en el propio repo

**Fecha:** 2026-10-18 | **Estado:** Activo

## Decisión

Los juegos seguidos (`data/follows.json`) y las decisiones sobre repos nuevos
(`data/review.json`) viven en el repo. La web los cambia haciendo commits con la API de
GitHub mediante un token *fine-grained* limitado a este repo y al permiso Contents, que el
usuario pega una vez por navegador y se guarda solo en ese navegador. Sin token, la web es
de solo lectura.

## Alternativas descartadas

- API en el miniserver: pasa por Cloudflare (afectada por DIGI) y requiere CORS + Access
  entre dos dominios.
- localStorage: no sincroniza entre móvil y PC.

## Por qué

Sincroniza entre dispositivos sin servidor y todo el tráfico va a GitHub, fuera del
alcance de la interceptación. Si el token se filtra, solo permite tocar este repo público
(se revoca en un clic). Que los favoritos sean visibles públicamente no importa.
