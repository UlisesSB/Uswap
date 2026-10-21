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

<div align="center">

### Apoya el proyecto

USwap es gratuito y de código abierto. Si te ahorra tiempo, puedes ayudarme a seguir mejorándolo:

**Alias bancario (Argentina): `uarodriguez.wb`** &nbsp;&middot;&nbsp; Titular: Ulises Agustin Rodriguez

<sub>Cualquier aporte, grande o chico, se agradece. Una estrella en GitHub o reportar un error ayuda igual.</sub>

</div>

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

- **Clic derecho, eliges y listo.** Se abre una mini terminal desde tu gestor de archivos, pulsas un número, se convierte y se cierra sola.
- **Una TUI completa cuando la necesitas.** Explora carpetas, convierte por lotes con barras de progreso y vigila una carpeta para convertir lo que llegue.
- **Pensado para el teclado.** Flechas _y_ teclas Vim (`j`/`k`, `g`/`G`, `/` para buscar, `Esc`).
- **Detecta el tipo real.** Usa _magic bytes_, no solo la extensión: un PNG renombrado a `.jpg` sigue siendo un PNG.
- **Privado.** Todo se ejecuta en local con Pillow, FFmpeg, Pandoc y Poppler.
- **Automatizable.** `uswap foto.heic --to jpg` funciona sin interfaz.
- **Estética limpia.** Sin emojis; glifos Unicode discretos (o ASCII puro) y cinco temas: Gruvbox, Nord, Catppuccin, Tokyo Night y Monokai.

## Instalación

### Windows

**Opción A - instalador (la más fácil).** Descarga **`USwap-Setup.exe`** desde la [página de Releases](https://github.com/UlisesSB/uswap/releases), ábrelo y pulsa _Siguiente_. Incluye todo (FFmpeg, Pandoc, Poppler), añade `uswap` al PATH y agrega _Convert with USwap_ al clic derecho. No necesita permisos de administrador.

**Opción B - desde el código, un solo comando.** Clona el repo y ejecuta el script. Instala Python (si falta), USwap, las herramientas y la entrada del clic derecho:

```powershell
git clone https://github.com/UlisesSB/uswap.git
cd uswap
powershell -ExecutionPolicy Bypass -File install.ps1
```

### Linux

Un solo comando tras clonar. Instala FFmpeg/Pandoc/Poppler (pregunta antes de usar `sudo`), USwap en un entorno virtual propio, el comando `uswap` y la entrada del clic derecho para Nautilus, Dolphin, Thunar y Nemo:

```bash
git clone https://github.com/UlisesSB/uswap.git
cd uswap
./install.sh
```

Opciones: `-y` (sin preguntas), `--no-system-deps`, `--no-menus`. Soporta `apt`, `dnf`, `pacman` y `zypper`.

### Desinstalar

- Windows: _Configuración > Aplicaciones > USwap > Desinstalar_ (instalador), o `install.ps1 -Uninstall`.
- Linux: `./install.sh --uninstall`

### Instalación manual (cualquier sistema)

USwap es un paquete de Python normal (3.10+): `pipx install .` o `pip install --user .`. En ese caso instala tú FFmpeg, Pandoc y Poppler y comprueba con `uswap --doctor`.

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

## Autor

Hecho por **YOUR NAME**.

- Portafolio: [uarodriguez.com](https://uarodriguez.com)
- GitHub: [@UlisesSB](https://github.com/UlisesSB)
- Correo: [uarodriguez@computer.org](mailto:uarodriguez@computer.org)

## Contribuir

Los _issues_ y _pull requests_ son bienvenidos. Lee antes [CONTRIBUTING.md](CONTRIBUTING.md).

## Licencia

[MIT](LICENSE) &copy; 2026 YOUR NAME

<p align="center"><sub>Creado por <a href="https://uarodriguez.com">uarodriguez.com</a></sub></p>
