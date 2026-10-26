<p align="center">
  <img src="assets/banner.png" alt="USwap" width="560">
</p>

<p align="center">
  <b>Convertí cualquier archivo desde el clic derecho o la terminal.</b><br>
  Imágenes, audio, video y documentos. Sin interfaz gráfica, sin internet, sin vueltas.
</p>

<p align="center">
  <img alt="Versión" src="https://img.shields.io/badge/versión-2.0.0-E8323F">
  <img alt="Plataformas" src="https://img.shields.io/badge/Windows%20%7C%20Linux-17161B">
  <img alt="Python" src="https://img.shields.io/badge/python-3.8%2B-17161B">
  <img alt="Licencia" src="https://img.shields.io/badge/licencia-MIT-FFB547">
</p>

<p align="center">
  <b>Español</b> · <a href="README.en.md">English</a>
</p>

---

Hacés clic derecho sobre un archivo, elegís **Convert with USwap**, se abre una terminal chiquita, tocás un número y listo: la copia convertida aparece al lado del original.

```text
  █  █ ▄▀▀▀▀    USwap  v2.0.0
  █  █ ▀▀▀▀▄    convert any file, right here
  ▀▄▄▀ ▄▄▄▄▀
  ─────────►
  ◄─────────

  file  vacaciones.mov
  type  QuickTime video  ·  48.2 MB

  convert to

  ► 1  MP4    MP4 video
    2  MKV    Matroska video
    3  WEBM   WebM video
    4  AVI    AVI video
    5  GIF    GIF image
    6  MP3    MP3 audio
    ...

  ↑↓ move   1-9 pick   Enter select   Esc back
```

## Qué hace

- **Detecta el tipo real del archivo.** Lee los primeros bytes en vez de confiar en la extensión: un PNG renombrado a `.jpg` se sigue tratando como PNG.
- **Nunca pisa nada.** El original queda intacto. Si `foto.jpg` ya existe, guarda `foto (1).jpg`.
- **Te muestra solo lo que tiene sentido.** Una foto ofrece formatos de imagen; un video ofrece video y también audio (para sacarle el sonido).
- **Convierte carpetas enteras.** Clic derecho sobre una carpeta, o la opción *Convert a folder* del menú, y pasás todas las imágenes a WebP de una.
- **Funciona sin conexión.** Todo pasa en tu computadora.
- **Es un solo archivo.** `uswap.py` usa solo la biblioteca estándar de Python; el trabajo pesado lo hacen [FFmpeg](https://ffmpeg.org), [Pandoc](https://pandoc.org) y [Poppler](https://poppler.freedesktop.org).

## Instalación

### Windows

Descargá **`USwap-Setup-2.0.0.exe`** desde [Releases](https://github.com/UlisesSB/USwap/releases/latest) y seguí el instalador. Ya trae FFmpeg, Pandoc y Poppler adentro, así que no tenés que instalar nada más. No pide permisos de administrador.

El instalador agrega:

- **Convert with USwap** al clic derecho de archivos y carpetas. En Windows 11 está dentro de *Mostrar más opciones*.
- USwap a **Enviar a**, para convertir varios archivos seleccionados juntos.
- El comando `uswap` a la terminal.

### Linux

```bash
git clone https://github.com/UlisesSB/USwap.git
cd USwap
bash install.sh
```

El instalador:

1. Instala Python 3, FFmpeg, Pandoc y Poppler con el gestor de paquetes de tu distro (`apt`, `dnf`, `pacman` o `zypper`). Te pregunta antes de usar `sudo`.
2. Copia USwap a `~/.local/share/uswap` y deja el comando `uswap` en `~/.local/bin`.
3. Agrega **Convert with USwap** al clic derecho de Nautilus (en *Scripts*), Nemo, Dolphin y Thunar.

No usa `pip` ni entornos virtuales, así que no se queda colgado bajando dependencias.

Para actualizar: `git pull && bash install.sh`. Para desinstalar: `bash install.sh --uninstall`.

> **Fedora:** el paquete `ffmpeg-free` no trae H.264. Para convertir a MP4/MKV/MOV, instalá el `ffmpeg` completo desde [RPM Fusion](https://rpmfusion.org).

## Uso

| Cómo | Qué pasa |
|---|---|
| Clic derecho › **Convert with USwap** | Elegís el formato con un número y se convierte. |
| `uswap` | Menú: convertir un archivo, convertir una carpeta, revisar herramientas. |
| `uswap foto.png` | Lo mismo que el clic derecho, desde la terminal. |
| `uswap foto.png --to webp` | Convierte directo, sin preguntar. |
| `uswap *.wav --to mp3` | Varios archivos a la vez. |
| `uswap Descargas/ --to jpg` | Todos los archivos compatibles de una carpeta. |
| `uswap --doctor` | Muestra qué herramientas están instaladas. |
| `uswap --formats` | Lista los formatos soportados. |

**Teclas:** `↑ ↓` o `j k` para moverte, `1`–`9` para elegir directo, `Enter` para confirmar, `Esc` o `q` para volver.

## Formatos

| Tipo | Entra | Sale | Motor |
|---|---|---|---|
| Imagen | png, jpg, webp, gif, bmp, tiff, ico | las mismas | FFmpeg |
| Audio | mp3, wav, flac, ogg, opus, m4a, aac | los mismos | FFmpeg |
| Video | mp4, mkv, webm, mov, avi | mp4, mkv, webm, mov, avi, gif y cualquier formato de audio | FFmpeg |
| Documento | docx, odt, rtf, epub, html, md, txt | los mismos | Pandoc |
| PDF | pdf | txt, png, jpg (una imagen por página) | Poppler |

## Apoyá el proyecto

USwap es libre y gratuito. Si te ahorra tiempo, podés darme una mano para seguir mejorándolo:

**Alias (Argentina): `uarodriguez.wb`** · Titular: Ulises Agustin Rodriguez

Una estrella en GitHub o reportar un error también ayuda un montón.

## Licencia

[MIT](LICENSE) © 2026 [Ulises Agustin Rodriguez](https://uarodriguez.com) · uarodriguez@computer.org

Podés usarlo, modificarlo y redistribuirlo libremente, siempre que mantengas el aviso de copyright. Las herramientas que trae el instalador de Windows tienen sus propias licencias: ver [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
