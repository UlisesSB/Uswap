#!/usr/bin/env bash
# USwap installer for Linux
#
#   git clone https://github.com/UlisesSB/USwap.git && cd USwap && ./install.sh
#
# 1. installs Python 3, FFmpeg, Pandoc and Poppler with your package manager (sudo)
# 2. copies uswap to ~/.local/share/uswap and links the `uswap` command in ~/.local/bin
# 3. adds "Convert with USwap" to the right-click menu (Nautilus, Nemo, Dolphin, Thunar)
#
# No pip, no virtualenv: USwap only uses the Python standard library.
#
#   ./install.sh              install or update
#   ./install.sh -y           do not ask before installing system packages
#   ./install.sh --uninstall  remove everything this script created
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
APP="$DATA/uswap"
BIN="$HOME/.local/bin"
LAUNCHER="$APP/open-in-terminal"
ICON="$DATA/icons/hicolor/256x256/apps/uswap.png"
DESKTOP="$DATA/applications/uswap.desktop"
LABEL="Convert with USwap"
NAUTILUS="$DATA/nautilus/scripts/$LABEL"
NEMO="$DATA/nemo/actions/uswap.nemo_action"
DOLPHIN="$DATA/kio/servicemenus/uswap.desktop"
THUNAR="${XDG_CONFIG_HOME:-$HOME/.config}/Thunar/uca.xml"

YES=0; UNINSTALL=0
for arg in "$@"; do
  case "$arg" in
    -y|--yes) YES=1 ;;
    --uninstall) UNINSTALL=1 ;;
    -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

if [ -t 1 ]; then R=$'\033[38;2;232;50;63m'; A=$'\033[38;2;255;181;71m'; D=$'\033[2m'; N=$'\033[0m'
else R=""; A=""; D=""; N=""; fi
step() { printf '%s►%s %s\n' "$R" "$N" "$*"; }
info() { printf '  %s%s%s\n' "$D" "$*" "$N"; }
have() { command -v "$1" >/dev/null 2>&1; }

remove_thunar() {
  [ -f "$THUNAR" ] && grep -q 'uswap:begin' "$THUNAR" || return 0
  awk '/<!-- uswap:begin -->/{s=1} !s{print} /<!-- uswap:end -->/{s=0}' "$THUNAR" > "$THUNAR.tmp"
  mv "$THUNAR.tmp" "$THUNAR"
}

if [ "$UNINSTALL" = 1 ]; then
  step "Removing USwap"
  rm -rf "$APP"
  rm -f "$BIN/uswap" "$ICON" "$DESKTOP" "$NAUTILUS" "$NEMO" "$DOLPHIN"
  remove_thunar
  info "done. FFmpeg, Pandoc and Poppler were left installed."
  exit 0
fi

printf '\n%s  █  █ ▄▀▀▀▀%s    USwap installer\n' "$R" "$N"
printf '%s  █  █ ▀▀▀▀▄%s    %sno pip, no virtualenv%s\n' "$R" "$N" "$D" "$N"
printf '%s  ▀▄▄▀ ▄▄▄▄▀%s\n%s  ─────────►%s\n%s  ◄─────────%s\n\n' "$R" "$N" "$R" "$N" "$A" "$N"

# ------------------------------------------------------------ system packages
step "Checking Python, FFmpeg, Pandoc and Poppler"
missing=()
have python3 && python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))' || missing+=(python)
have ffmpeg   || missing+=(ffmpeg)
have pandoc   || missing+=(pandoc)
have pdftoppm || missing+=(poppler)

if [ ${#missing[@]} -eq 0 ]; then
  info "everything is already installed"
else
  if   have apt-get; then pm=apt;    names=(python3 ffmpeg pandoc poppler-utils)
  elif have dnf;     then pm=dnf;    names=(python3 ffmpeg-free pandoc poppler-utils)
  elif have pacman;  then pm=pacman; names=(python ffmpeg pandoc-cli poppler)
  elif have zypper;  then pm=zypper; names=(python3 ffmpeg pandoc poppler-tools)
  else pm=""; fi
  pkgs=()
  for m in "${missing[@]}"; do
    case "$m" in
      python) pkgs+=("${names[0]}") ;; ffmpeg) pkgs+=("${names[1]}") ;;
      pandoc) pkgs+=("${names[2]}") ;; poppler) pkgs+=("${names[3]}") ;;
    esac
  done
  if [ -z "$pm" ]; then
    info "no known package manager. Install these yourself: ${missing[*]}"
  else
    answer=y
    if [ "$YES" = 0 ] && [ -t 0 ]; then
      read -r -p "  Install ${pkgs[*]} with $pm (needs sudo)? [Y/n] " answer || true
    fi
    case "${answer:-y}" in
      [nN]*) info "skipped: some formats will not work until you install ${pkgs[*]}" ;;
      *) case "$pm" in
           apt)    sudo apt-get update -qq && sudo apt-get install -y "${pkgs[@]}" ;;
           dnf)    sudo dnf install -y "${pkgs[@]}" ;;
           pacman) sudo pacman -S --needed --noconfirm "${pkgs[@]}" ;;
           zypper) sudo zypper --non-interactive install "${pkgs[@]}" ;;
         esac || info "some packages failed; run 'uswap --doctor' afterwards" ;;
    esac
  fi
fi
have python3 || { echo "error: USwap needs Python 3.8 or newer." >&2; exit 1; }

# ----------------------------------------------------------------- the program
step "Installing USwap"
mkdir -p "$APP" "$BIN" "$(dirname "$ICON")" "$(dirname "$DESKTOP")"
install -m 755 "$REPO/uswap.py" "$APP/uswap.py"
ln -sf "$APP/uswap.py" "$BIN/uswap"
cp "$REPO/assets/logo.png" "$ICON"
info "$("$APP/uswap.py" --version)  →  $BIN/uswap"

# File managers start programs without a terminal, so this opens one.
cat > "$LAUNCHER" <<'EOF'
#!/usr/bin/env bash
USWAP="$(dirname "$(readlink -f "$0")")/uswap.py"
for t in "${TERMINAL:-}" x-terminal-emulator gnome-terminal kgx ptyxis konsole xfce4-terminal \
         mate-terminal tilix kitty alacritty foot wezterm lxterminal xterm; do
  [ -n "$t" ] && command -v "$t" >/dev/null 2>&1 && break; t=""
done
[ -n "$t" ] || { notify-send "USwap" "No terminal emulator found" 2>/dev/null; exit 1; }
case "$(basename "$t")" in
  gnome-terminal|kgx|ptyxis|tilix) exec "$t" -- "$USWAP" "$@" ;;
  xfce4-terminal|mate-terminal|lxterminal) exec "$t" -x "$USWAP" "$@" ;;
  kitty|foot) exec "$t" "$USWAP" "$@" ;;
  wezterm) exec "$t" start -- "$USWAP" "$@" ;;
  *) exec "$t" -e "$USWAP" "$@" ;;
esac
EOF
chmod 755 "$LAUNCHER"

cat > "$DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=USwap
Comment=Convert images, audio, video and documents
Exec=$BIN/uswap %F
Icon=uswap
Terminal=true
Categories=Utility;
EOF

# ------------------------------------------------------------ right-click menu
step "Adding \"$LABEL\" to the right-click menu"
found=0
if have nautilus; then
  mkdir -p "$(dirname "$NAUTILUS")"
  cat > "$NAUTILUS" <<EOF
#!/usr/bin/env bash
mapfile -t files <<< "\${NAUTILUS_SCRIPT_SELECTED_FILE_PATHS%$'\\n'}"
exec "$LAUNCHER" "\${files[@]}"
EOF
  chmod 755 "$NAUTILUS"
  info "Nautilus  →  right-click › Scripts › $LABEL"; found=1
fi
if have nemo; then
  mkdir -p "$(dirname "$NEMO")"
  printf '[Nemo Action]\nName=%s\nExec=%s %%F\nIcon-Name=uswap\nSelection=notnone\nExtensions=any;dir;\n' \
    "$LABEL" "$LAUNCHER" > "$NEMO"
  info "Nemo      →  right-click › $LABEL"; found=1
fi
if have dolphin; then
  mkdir -p "$(dirname "$DOLPHIN")"
  cat > "$DOLPHIN" <<EOF
[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=application/octet-stream;inode/directory;
Actions=uswap;
X-KDE-Priority=TopLevel

[Desktop Action uswap]
Name=$LABEL
Icon=uswap
Exec=$LAUNCHER %F
EOF
  chmod 755 "$DOLPHIN"
  info "Dolphin   →  right-click › $LABEL"; found=1
fi
if have thunar; then
  mkdir -p "$(dirname "$THUNAR")"
  remove_thunar
  block="<!-- uswap:begin -->
<action><icon>uswap</icon><name>$LABEL</name><unique-id>uswap-2</unique-id>
<command>$LAUNCHER %F</command><description>Convert with USwap</description><patterns>*</patterns>
<audio-files/><image-files/><other-files/><text-files/><video-files/><directories/></action>
<!-- uswap:end -->"
  if [ -f "$THUNAR" ]; then
    awk -v b="$block" '/<\/actions>/ && !d {print b; d=1} {print}' "$THUNAR" > "$THUNAR.tmp"
    mv "$THUNAR.tmp" "$THUNAR"
  else
    printf '<?xml version="1.0" encoding="UTF-8"?>\n<actions>\n%s\n</actions>\n' "$block" > "$THUNAR"
  fi
  info "Thunar    →  right-click › $LABEL  (restart it: thunar -q)"; found=1
fi
[ "$found" = 1 ] || info "no supported file manager found; you can still use the uswap command"

# ------------------------------------------------------------------------ done
echo
step "Done"
"$BIN/uswap" --doctor || true
case ":$PATH:" in
  *":$BIN:"*) ;;
  *) echo; info "$BIN is not in your PATH. Add this line to ~/.bashrc and open a new terminal:"
     printf '    %sexport PATH="$HOME/.local/bin:$PATH"%s\n' "$A" "$N" ;;
esac
echo
info "try it:  uswap        (or right-click any file › $LABEL)"
info "update:  git pull && ./install.sh"
