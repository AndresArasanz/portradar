# Ficha — portradar

> Se rellena y se aprueba **antes** de escribir código. Si el alcance cambia, se actualiza la ficha primero.

## Resumen

Una web propia en `ports.ibaietarra.com` que sigue los ports nativos no oficiales
de juegos de consola a PC que salen en GitHub, de cualquier plataforma
(Bloodborne y Shadow of the Colossus de PS4, Burnout 3 de PS2/Xbox, Zelda de
Switch…). Muestra de cada uno su estado, última versión, estrellas y última
actividad, se actualiza sola cada día sin IA y avisa de repos nuevos para
revisarlos a mano. Permite marcar qué juegos sigo y vigilar juegos anunciados
que aún no tienen repo.

> Ampliado a todas las plataformas en el issue #1 (2026-10-22). Antes solo PS4.

## Alcance

- Web estática en GitHub Pages (repo público `AndresArasanz/portradar`) con dominio `ports.ibaietarra.com` (CNAME en Cloudflare **sin proxy**). Ver ADR-001.
- Tres pestañas: **Siguiendo** (solo los que marco), **Todos** y **Sin revisar** (repos nuevos detectados).
- Por juego: nombre, repo (enlace), sistema, estado (Jugable / Alfa / Temprano), **hasta dónde llega**, nota, última release y su fecha, estrellas y último cambio (`pushed_at`). Búsqueda y orden por columna, como la versión de prueba.
- Datos de partida: los 16 ports de la versión de prueba (`data/ports.json`). Estado, hasta dónde llega, nota y sistema son **manuales**; el resto es automático.
- **Extracto del "Status" del README**: el recolector copia la línea/párrafo de estado que publica el autor (sección `## Status` o línea `**Status: …**`) y la web lo muestra bajo el juego con enlace al README. Si el repo no tiene, no se muestra nada.
- **Aviso "estado cambiado"**: si ese extracto cambia respecto a la ejecución anterior se guarda la fecha y la fila se marca durante 7 días.
- Sin porcentajes: estos ports son recompilaciones, no descompilaciones; no se inventa un % a partir de commits o releases.
- Actualización diaria con **GitHub Actions** (cron) usando el `GITHUB_TOKEN` del workflow: estrellas, última release, `pushed_at`, archivado, renombrado/desaparecido y si es fork. Hace commit de `data/` solo si hay cambios. Ver ADR-002.
- Detección de repos nuevos con varias búsquedas en la API de GitHub (`ps4 pc port`, `ps4 recomp`, `native pc port ps4`…), excluyendo forks y repos ya conocidos o descartados; entran como **"nuevo, sin revisar"**.
- Seguir / dejar de seguir y Aceptar / Descartar repos nuevos desde la web: se guardan en el repo (`data/follows.json`, `data/review.json`) mediante la API de GitHub con un token *fine-grained* (solo este repo, solo Contents) que se pega una vez por navegador. Ver ADR-003.
- Sin token en el navegador la web funciona en modo solo lectura.
- Aviso de seguridad visible: descargar solo desde la pestaña Releases del repo original, nunca de forks con `.exe`. Los repos que sean fork llevan una etiqueta neutra "fork de <repo origen>" (ser fork no implica peligro: Bloodborne Windows, God of War III y Gran Turismo son forks).
- Tema claro/oscuro y usable en móvil (diseño de la versión de prueba).

### Ampliación a todas las plataformas (issue #1)

- **Plataforma de origen** por juego (`platform` en `ports.json`, manual): PS4, PS3, PS2, PS1, Xbox, Xbox 360, Switch, Wii U, Wii, GameCube, N64, PSP, 3DS, DS, otra. Los 16 existentes pasan a `PS4`. Columna visible y **filtro por plataforma** en la web, combinable con las pestañas y la búsqueda.
- **Tipo** por juego (`kind`, manual): `port` (ejecutable jugable: recompilación o decomp con port) o `decomp` (código reconstruido sin ejecutable jugable todavía). Se muestra como etiqueta; la pestaña Siguiendo no filtra por tipo.
- **Búsquedas ampliadas** del recolector: se mantienen las de PS4 y se añaden términos genéricos (`static recompilation`, `recomp pc port`, `native pc port`, `decompilation pc port`, `decomp`) y por plataforma (`ps2 pc port`, `xbox recomp`, `switch recomp`, `n64 recomp`…). Para no inundar *Sin revisar*, los resultados de búsquedas genéricas solo entran con **≥ 10 estrellas** y como mucho **20 candidatos nuevos por ejecución** (los de más estrellas primero). Las búsquedas de PS4 de siempre no tienen mínimo.
- **Vigilados** (`data/watch.json`, manual): juegos anunciados sin repo conocido, con nombre y palabras clave (p. ej. ToTK: `tears of the kingdom`, `totk`). El recolector busca esas palabras cada día **sin mínimo de estrellas**; si aparece un repo que encaja, entra en *Sin revisar* con la marca "vigilado: <juego>" y la pestaña muestra cuántos hay. Los vigilados se ven en una lista corta dentro de *Sin revisar* ("esperando repo"). Al Aceptar el repo, el vigilado se da por cumplido y se quita de la lista.
- **Datos que se añaden**: Takedawn (`xenophobentx/takedawn`, Xbox, port) y burnout3-pc (`danielgomesvieira2000/burnout3-pc`, PS2, port) en `ports.json`; ToTK como vigilado.
- **Agregadores existentes** (PlayPorted, RecompHub, Duskport): ya hacen un catálogo general, pero ninguno ofrece API pública (PlayPorted prohíbe `/api/` en `robots.txt`) ni favoritos/avisos propios. PortRadar sigue usando solo la API de GitHub; no se rastrean esas webs. Ver ADR-004.

## Fuera de alcance

- Backend propio o alojamiento en el miniserver (descartado en ADR-001).
- Calcular el estado "Jugable/Alfa/Temprano" automáticamente o con IA.
- Descargar, analizar o enlazar binarios; escanear releases en busca de malware.
- Notificaciones (Ntfy, email) de versiones o repos nuevos — posible mejora futura, no ahora.
- Login de usuarios o multiusuario.
- ~~Otras plataformas~~ — incorporadas en el issue #1.
- Rastrear o copiar datos de agregadores (PlayPorted, RecompHub, Duskport, decomp.dev) — ADR-004.
- Porcentajes de progreso de decomps (los publica decomp.dev; no se replican).
- Ports que no están en GitHub (X/Twitter, Discord, itch.io): un vigilado avisa solo cuando aparece repo en GitHub.

## Criterios de aceptación (comprobables)

- [ ] `https://ports.ibaietarra.com` carga con HTTPS válido de GitHub Pages (no Cloudflare) y muestra los 16 ports de partida.
- [ ] Las pestañas Siguiendo / Todos / Sin revisar filtran correctamente; Siguiendo muestra solo lo de `follows.json`.
- [ ] Con el token pegado, marcar/desmarcar un juego crea un commit en `data/follows.json` y se ve igual desde otro dispositivo tras recargar.
- [ ] Sin token, no aparece ningún control de escritura y no hay errores en consola.
- [ ] El workflow diario se ejecuta solo, actualiza estrellas/release/`pushed_at` y no hace commit si no hay cambios.
- [ ] Un repo que encaja en la búsqueda y no está en la lista aparece en Sin revisar; al Descartarlo no vuelve a aparecer en la siguiente ejecución; al Aceptarlo pasa a Todos.
- [ ] Los repos con sección de estado en el README (p. ej. CTR, UFC 3, Unicorn Overlord) muestran su extracto; los que no tienen, no muestran nada.
- [ ] Si el extracto cambia entre dos ejecuciones, la fila aparece marcada como "estado cambiado".
- [ ] Un repo que devuelve 404 o está archivado se marca como tal en la tabla en vez de romper el workflow.
- [ ] El aviso de seguridad está visible sin hacer scroll en Todos, y los forks llevan la etiqueta "fork de <origen>".
- [ ] Ningún token ni secreto en el repo (comprobado con `git grep` y con el historial).

**Ampliación (issue #1):**

- [ ] Los 16 ports de PS4 siguen apareciendo igual y llevan plataforma `PS4`.
- [ ] Takedawn y burnout3-pc aparecen en *Todos* con plataforma Xbox / PS2 y sus estrellas, release y `pushed_at` automáticos.
- [ ] El filtro por plataforma muestra solo los de esa plataforma y se combina con pestaña y búsqueda.
- [ ] Un repo de una búsqueda genérica con < 10 estrellas no entra en *Sin revisar*; uno de PS4 con 0 estrellas sí.
- [ ] Una ejecución no añade más de 20 candidatos nuevos de búsquedas genéricas.
- [ ] Un repo (simulado en test) que contiene las palabras de un vigilado entra en *Sin revisar* marcado "vigilado: <juego>" aunque tenga 0 estrellas.
- [ ] ToTK aparece en la lista "esperando repo"; al Aceptar su repo desaparece de esa lista.
- [ ] `ports.json` y `watch.json` con plataforma, tipo o campos inválidos hacen fallar la validación en CI.

## Tests que deben pasar

- Recolector (Python, pytest, API de GitHub simulada): mapeo de respuesta → registro; repo 404 / archivado / renombrado; sin releases; detección de forks; extracción del Status (sección, línea en negrita, ausente, recorte de longitud); detección de cambio de estado; búsqueda filtra conocidos, descartados y forks; no reescribe datos si no hay cambios.
- Validación del esquema de `ports.json`, `follows.json` y `review.json` (también en CI antes de commit).
- Web (JS, unit): filtros por pestaña, orden por columna, fechas relativas, modo solo lectura sin token.
- E2E (Playwright) sobre la web local: carga, cambio de pestañas, búsqueda.
- Ampliación: validación de `platform`/`kind`/`watch.json`; mínimo de estrellas y tope de 20 en búsquedas genéricas; coincidencia con vigilados (palabras en nombre/descripción, sin distinguir mayúsculas); vigilado cumplido al aceptar; filtro por plataforma (unit JS + E2E).

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
