<p align="center">
  <img src="assets/banner.png" alt="USwap" width="520">
</p>

<p align="center">
  <b>Conversor de archivos ligero para tu terminal, pensado para el teclado.</b><br>
  Im&aacute;genes, audio, v&iacute;deo y documentos &mdash; 100&nbsp;% sin conexi&oacute;n, sin interfaces gr&aacute;ficas pesadas.
</p>

<p align="center">
  <a href="README.md">English</a> &middot; Espa&ntilde;ol
</p>

---

```text
╭─────────────╮
│  █  █ █▀▀▀  │   USwap v0.1.0
│  █  █ ▀▀▀█  │   Motor de conversión de archivos
│  ▀▄▄▀ █▄▄█  │   ────────────────────────────────
│      ⇄      │   Comando: uswap
╰─────────────╯
```

## ¿Por qué USwap?

* **Clic derecho, eliges y listo.** Se abre una mini terminal desde tu gestor de archivos, pulsas un número, se convierte y se cierra sola.
* **Una TUI completa cuando la necesitas.** Explora carpetas, convierte por lotes con barras de progreso y vigila una carpeta para convertir lo que llegue.
* **Pensado para el teclado.** Flechas *y* teclas Vim (`j`/`k`, `g`/`G`, `/` para buscar, `Esc`).
* **Detecta el tipo real.** Usa *magic bytes*, no solo la extensión: un PNG renombrado a `.jpg` sigue siendo un PNG.
* **Privado.** Todo se ejecuta en local con Pillow, FFmpeg, Pandoc y Poppler.
* **Automatizable.** `uswap foto.heic --to jpg` funciona sin interfaz.
* **Estética limpia.** Sin emojis; glifos Unicode discretos (o ASCII puro) y cinco temas: Gruvbox, Nord, Catppuccin, Tokyo Night y Monokai.

## Instalación

Necesitas **Python 3.10+**. Lo recomendado es [pipx](https://pipx.pypa.io/), que lo aísla y deja `uswap` en tu `PATH`:

```bash
git clone https://github.com/YOUR-USER/uswap.git
cd uswap
pipx install .
```

O con pip: `pip install --user .`

### Herramientas externas (opcionales)

Las imágenes funcionan sin instalar nada más. Instala el resto solo para los formatos que necesites:

| Herramienta | Habilita | Debian/Ubuntu | Windows |
|-------------|----------|---------------|---------|
| FFmpeg | audio y vídeo | `sudo apt install ffmpeg` | `winget install Gyan.FFmpeg` |
| Pandoc | documentos | `sudo apt install pandoc` | `winget install JohnMacFarlane.Pandoc` |
| Poppler | PDF a texto/imágenes | `sudo apt install poppler-utils` | `scoop install poppler` |

Ejecuta `uswap --doctor` para ver qué tienes instalado (más distros en el [README en inglés](README.md#install)).

### Menú contextual (clic derecho)

**Linux** (Nautilus, Dolphin, Thunar, Nemo):

```bash
./scripts/install.sh            # --all para instalar en todos
./scripts/install.sh --uninstall
```

**Windows** (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install.ps1
powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Uninstall
```

## Uso

```text
uswap                     abre el panel principal
uswap ARCHIVO             mini ventana para un archivo
uswap ARCHIVO ARCHIVO ... modo lotes (un formato de salida para todos)
uswap ARCHIVO --to FORMATO  convierte sin interfaz (admite comodines y carpetas)
uswap --watch CARPETA     convierte automáticamente lo que llegue a la carpeta
uswap --config            panel de ajustes
uswap --doctor            comprueba dependencias
uswap --formats           lista los formatos soportados
```

Ejemplos:

```bash
uswap cancion.wav                      # mini ventana interactiva
uswap "*.png" --to webp -o ./salida    # sin interfaz, carpeta de salida propia
uswap ~/Imágenes --to jpg -j 8         # todos los archivos soportados de una carpeta
uswap --watch ~/Descargas --rule heic:jpg --rule image:webp
```

## Configuración

Se guarda en `~/.config/uswap/config.json` (Linux) o `%APPDATA%\uswap\config.json` (Windows) y se edita desde `uswap --config`: idioma (EN/ES), tema, carpeta de salida, regla de nombres, calidad de imagen, hilos y reglas del vigilante.

## Documentación

La documentación técnica completa (en inglés) está en [`docs/`](docs/): instalación, uso, configuración, menús contextuales, arquitectura y guía de desarrollo.

## Contribuir

Los *issues* y *pull requests* son bienvenidos. Lee antes [CONTRIBUTING.md](CONTRIBUTING.md).

## Licencia

[MIT](LICENSE) &copy; 2026 YOUR NAME

<p align="center"><sub>Hecho por <a href="https://github.com/YOUR-USER">YOUR NAME</a> &middot; <a href="mailto:you@example.com">you@example.com</a></sub></p>
