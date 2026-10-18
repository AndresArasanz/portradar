# ADR-001 — Alojar en GitHub Pages con dominio sin proxy de Cloudflare

**Fecha:** 2026-10-18 | **Estado:** Activo

## Decisión

La web es estática y se sirve desde GitHub Pages (repo público `AndresArasanz/portradar`)
con el dominio `ports.ibaietarra.com` como CNAME a `andresarasanz.github.io`,
**sin proxy de Cloudflare** (nube gris). El HTTPS lo pone GitHub Pages.

## Alternativas descartadas

- Miniserver + Cloudflare Tunnel: permite backend propio, pero DIGI intercepta el TLS
  hacia los rangos de Cloudflare (comprobado activo el 2026-10-18) y fuera de casa la web
  se cortaría; además depende de que el miniserver esté encendido.
- Cloudflare Pages: igual de afectado por la interceptación y sin poder usar split-horizon.

## Por qué

Pages no pasa por Cloudflare, así que es inmune a la interceptación de DIGI, no depende
del miniserver y no hay infraestructura que mantener. El precio es que el repo es público,
lo que no importa: los datos son públicos de por sí.
