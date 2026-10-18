# Ficha — portradar

> Se rellena y se aprueba **antes** de escribir código. Si el alcance cambia, se actualiza la ficha primero.

## Resumen

Una web propia en `ports.ibaietarra.com` que sigue los ports nativos no oficiales
de juegos de PS4 a PC que salen en GitHub (Bloodborne, Shadow of the Colossus,
God of War III, Uncharted…). Muestra de cada uno su estado, última versión,
estrellas y última actividad, se actualiza sola cada día sin IA y avisa de
repos nuevos para revisarlos a mano. Permite marcar qué juegos sigo.

## Alcance

- Web estática en GitHub Pages (repo público `AndresArasanz/portradar`) con dominio `ports.ibaietarra.com` (CNAME en Cloudflare **sin proxy**). Ver ADR-001.
- Tres pestañas: **Siguiendo** (solo los que marco), **Todos** y **Sin revisar** (repos nuevos detectados).
- Por juego: nombre, repo (enlace), sistema, estado (Jugable / Alfa / Temprano), nota, última release y su fecha, estrellas y último cambio (`pushed_at`). Búsqueda y orden por columna, como la versión de prueba.
- Datos de partida: los 16 ports de la versión de prueba (`data/ports.json`). Estado, nota y sistema son **manuales**; el resto es automático.
- Actualización diaria con **GitHub Actions** (cron) usando el `GITHUB_TOKEN` del workflow: estrellas, última release, `pushed_at`, archivado, renombrado/desaparecido y si es fork. Hace commit de `data/` solo si hay cambios. Ver ADR-002.
- Detección de repos nuevos con varias búsquedas en la API de GitHub (`ps4 pc port`, `ps4 recomp`, `native pc port ps4`…), excluyendo forks y repos ya conocidos o descartados; entran como **"nuevo, sin revisar"**.
- Seguir / dejar de seguir y Aceptar / Descartar repos nuevos desde la web: se guardan en el repo (`data/follows.json`, `data/review.json`) mediante la API de GitHub con un token *fine-grained* (solo este repo, solo Contents) que se pega una vez por navegador. Ver ADR-003.
- Sin token en el navegador la web funciona en modo solo lectura.
- Aviso de seguridad visible: descargar solo desde la pestaña Releases del repo original, nunca de forks con `.exe`. Los repos que sean fork llevan una etiqueta "fork" automática.
- Tema claro/oscuro y usable en móvil (diseño de la versión de prueba).

## Fuera de alcance

- Backend propio o alojamiento en el miniserver (descartado en ADR-001).
- Calcular el estado "Jugable/Alfa/Temprano" automáticamente o con IA.
- Descargar, analizar o enlazar binarios; escanear releases en busca de malware.
- Notificaciones (Ntfy, email) de versiones o repos nuevos — posible mejora futura, no ahora.
- Login de usuarios o multiusuario.
- Otras plataformas (PS2/PS3/Xbox, decomp.dev, N64Recomp…).

## Criterios de aceptación (comprobables)

- [ ] `https://ports.ibaietarra.com` carga con HTTPS válido de GitHub Pages (no Cloudflare) y muestra los 16 ports de partida.
- [ ] Las pestañas Siguiendo / Todos / Sin revisar filtran correctamente; Siguiendo muestra solo lo de `follows.json`.
- [ ] Con el token pegado, marcar/desmarcar un juego crea un commit en `data/follows.json` y se ve igual desde otro dispositivo tras recargar.
- [ ] Sin token, no aparece ningún control de escritura y no hay errores en consola.
- [ ] El workflow diario se ejecuta solo, actualiza estrellas/release/`pushed_at` y no hace commit si no hay cambios.
- [ ] Un repo que encaja en la búsqueda y no está en la lista aparece en Sin revisar; al Descartarlo no vuelve a aparecer en la siguiente ejecución; al Aceptarlo pasa a Todos.
- [ ] Un repo que devuelve 404 o está archivado se marca como tal en la tabla en vez de romper el workflow.
- [ ] El aviso de seguridad está visible sin hacer scroll en Todos, y los forks llevan la etiqueta "fork".
- [ ] Ningún token ni secreto en el repo (comprobado con `git grep` y con el historial).

## Tests que deben pasar

- Recolector (Python, pytest, API de GitHub simulada): mapeo de respuesta → registro; repo 404 / archivado / renombrado; sin releases; detección de forks; búsqueda filtra conocidos, descartados y forks; no reescribe datos si no hay cambios.
- Validación del esquema de `ports.json`, `follows.json` y `review.json` (también en CI antes de commit).
- Web (JS, unit): filtros por pestaña, orden por columna, fechas relativas, modo solo lectura sin token.
- E2E (Playwright) sobre la web local: carga, cambio de pestañas, búsqueda.

## Dependencias

- Cuenta GitHub `AndresArasanz` vía `gh` (crear repo, push, activar Pages) — **requiere confirmación**: repo público.
- Registro DNS `ports` CNAME → `andresarasanz.github.io` en Cloudflare, sin proxy — **requiere confirmación**.
- Token fine-grained para escribir favoritos: lo crea el usuario en GitHub (instrucciones en el README); nunca se guarda en el repo.

## Terminado (checklist de cierre)

- [ ] Tests en verde (cobertura ≥ 80 % en lo nuevo)
- [ ] Criterios de aceptación comprobados uno a uno
- [ ] `CHANGELOG.md` actualizado en lenguaje normal
- [ ] `README.md` al día (cómo se usa, URL/puerto)
- [ ] ADR escrito si hubo una decisión no obvia
- [ ] Sin secretos en git (`git grep` de tokens/contraseñas, `.env` ignorado)
- [ ] Si es servicio: `CLAUDE_CONTEXT.md`, `homer/config.yml` y `dashboard/main.py` actualizados
