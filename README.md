<p align="center">
  <img src="assets/banner.png" alt="USwap" width="560">
</p>

<p align="center">
  <b>Convertí cualquier archivo desde el clic derecho o la terminal.</b><br>
  Imágenes, audio, video y documentos. Sin interfaz gráfica, sin internet, sin vueltas.
</p>

<p align="center">
  <img alt="Versión" src="https://img.shields.io/badge/versión-2.1.0-E8323F">
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
  █  █ ▄▀▀▀▀    USwap  v2.1.0
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
- **Te muestra solo lo que tiene sentido.** Una foto ofrece formatos de imagen y PDF; un video ofrece video y también audio (para sacarle el sonido).
- **Convierte carpetas enteras.** Clic derecho sobre una carpeta, o *Convert a folder* en el menú, y pasás todas las imágenes a WebP de una, o las juntás en un solo PDF.
- **Liviano por defecto.** La base solo necesita FFmpeg. Los formatos menos comunes son *complementos* que instalás desde el menú si los necesitás.
- **Funciona sin conexión.** Todo pasa en tu computadora. Solo usa internet si instalás un complemento o una actualización.
- **Es un solo archivo.** `uswap.py` usa solo la biblioteca estándar de Python.

## Instalación

### Windows

Descargá **`USwap-Setup-2.1.0.exe`** desde [Releases](https://github.com/UlisesSB/USwap/releases/latest) y seguí el instalador. Ya trae FFmpeg, así que imágenes, audio y video funcionan desde el primer momento. No pide permisos de administrador.

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

1. Instala Python 3 y FFmpeg con el gestor de paquetes de tu distro (`apt`, `dnf`, `pacman` o `zypper`), si te faltan. Te pregunta antes de usar `sudo`.
2. Copia USwap a `~/.local/share/uswap` y deja el comando `uswap` en `~/.local/bin`.
3. Agrega **Convert with USwap** al clic derecho de Nautilus (en *Scripts*), Nemo, Dolphin y Thunar.

No usa `pip` ni entornos virtuales. Para desinstalar: `bash install.sh --uninstall`.

> **Fedora:** el paquete `ffmpeg-free` no trae H.264. Para convertir a MP4/MKV/MOV, instalá el `ffmpeg` completo desde [RPM Fusion](https://rpmfusion.org).

## Formatos opcionales

Abrí `uswap` y elegí **Optional formats**. Cada complemento se instala solo si lo elegís, y se puede quitar después.

| Complemento | Qué agrega | De dónde sale |
|---|---|---|
| **Documents** | docx, odt, md, html, rtf, epub y txt entre sí | [Pandoc](https://pandoc.org), descarga directa |
| **PDF reader** | pdf → txt, png, jpg (una imagen por página) | [Poppler](https://poppler.freedesktop.org) |
| **Documents to PDF** | md, docx, html, epub… → pdf | [Typst](https://typst.app), descarga directa (usa Documents) |
| **Extra images** | heic (fotos de iPhone), avif, svg → cualquier imagen o pdf | [ImageMagick](https://imagemagick.org) |
| **Office to PDF** | docx, xlsx, pptx, odt… → pdf idéntico al original | [LibreOffice](https://libreoffice.org) (pesado) |

Los de "descarga directa" se bajan de la página oficial de cada proyecto a la carpeta de USwap, sin permisos de administrador. Los demás usan el gestor de paquetes de Linux o `winget` en Windows. También se instalan desde la terminal: `uswap --install documents`.

Si abrís un archivo que necesita un complemento que no tenés, USwap te dice cuál instalar.

## Uso

| Cómo | Qué pasa |
|---|---|
| Clic derecho › **Convert with USwap** | Elegís el formato con un número y se convierte. |
| `uswap` | Menú: convertir un archivo o una carpeta, formatos opcionales, revisar herramientas. |
| `uswap foto.png` | Lo mismo que el clic derecho, desde la terminal. |
| `uswap foto.png --to webp` | Convierte directo, sin preguntar. |
| `uswap *.jpg --to pdf --merge` | Junta varias imágenes en un solo PDF. |
| `uswap Descargas/ --to jpg` | Todos los archivos compatibles de una carpeta. |
| `uswap --install NOMBRE` | Instala un complemento (`documents`, `pdf`, `docpdf`, `images`, `office`). |
| `uswap --doctor` | Muestra qué herramientas y complementos están instalados. |
| `uswap --formats` | Lista los formatos soportados. |
| `uswap --update` | Actualiza USwap, solo si confirmás. |

**Teclas:** `↑ ↓` o `j k` para moverte, `1`–`9` para elegir directo, `Enter` para confirmar, `Esc` o `q` para volver.

## Formatos

| Tipo | Entra | Sale | Necesita |
|---|---|---|---|
| Imagen | png, jpg, webp, gif, bmp, tiff, ico | las mismas y pdf | — |
| Imagen | heic, avif, svg | png, jpg, webp, gif, bmp, tiff, ico, pdf | Extra images |
| Audio | mp3, wav, flac, ogg, opus, m4a, aac, wma, aiff, amr | mp3, wav, flac, ogg, opus, m4a, aac | — |
| Video | mp4, mkv, webm, mov, avi, wmv, flv, 3gp, mpeg, ts | mp4, mkv, webm, mov, avi, gif y cualquier audio | — |
| Documento | docx, odt, rtf, epub, html, md, txt | los mismos | Documents |
| Documento | docx, odt, rtf, epub, html, md, txt | pdf | Documents to PDF |
| Office | docx, doc, xlsx, xls, pptx, ppt, odt, ods, odp, rtf | pdf | Office to PDF |
| PDF | pdf | txt, png, jpg | PDF reader |

## Actualizaciones

USwap revisa una vez por día si hay una versión nueva y, si la hay, muestra un aviso discreto (`▲ v2.2.0 available`) en el menú. No descarga ni cambia nada por su cuenta.

Para actualizar, corré `uswap --update`, o elegí *Update* en el menú, y confirmá:

- **Windows:** baja el instalador nuevo y lo abre.
- **Linux (instalado con `git clone`):** hace `git pull` y vuelve a correr `install.sh`.

Si no querés que revise nada, definí la variable de entorno `USWAP_NO_UPDATE_CHECK=1`.

## Apoyá el proyecto

USwap es libre y gratuito. Si te ahorra tiempo, podés darme una mano para seguir mejorándolo:

**Alias (Argentina): `uarodriguez.wb`** · Titular: Ulises Agustin Rodriguez

Una estrella en GitHub o reportar un error también ayuda un montón.

## Licencia

[MIT](LICENSE) © 2026 [Ulises Agustin Rodriguez](https://uarodriguez.com) · uarodriguez@computer.org

Podés usarlo, modificarlo y redistribuirlo libremente, siempre que mantengas el aviso de copyright. FFmpeg (incluido en el instalador de Windows) y los complementos tienen sus propias licencias: ver [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
