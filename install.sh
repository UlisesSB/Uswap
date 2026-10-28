#!/usr/bin/env bash
# USwap installer for Linux
#
#   git clone https://github.com/UlisesSB/USwap.git && cd USwap && bash install.sh
#
# 1. installs Python 3 and FFmpeg with your package manager (sudo), if missing
# 2. copies uswap to ~/.local/share/uswap and links the `uswap` command in ~/.local/bin
# 3. adds "Convert with USwap" to the right-click menu (Nautilus, Nemo, Dolphin, Thunar)
#
# Extra formats (documents, PDF, iPhone photos, Office) are optional add-ons:
# open `uswap` and choose "Optional formats" whenever you want them.
#
#   bash install.sh              install or update
#   bash install.sh -y           do not ask before installing system packages
#   bash install.sh --uninstall  remove everything this script created
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
APP="$DATA/uswap"
BIN="$HOME/.local/bin"
ICON="$DATA/icons/hicolor/256x256/apps/uswap.png"
DESKTOP="$DATA/applications/uswap.desktop"
LABEL="Convert with USwap"
NAUTILUS="$DATA/nautilus/scripts/$LABEL"
NEMO="$DATA/nemo/actions/uswap.nemo_action"
DOLPHIN="$DATA/kio/servicemenus/uswap.desktop"
THUNAR="${XDG_CONFIG_HOME:-$HOME/.config}/Thunar/uca.xml"
RUN="$BIN/uswap --terminal"

YES=0; UNINSTALL=0
for arg in "$@"; do
  case "$arg" in
    -y|--yes) YES=1 ;;
    --uninstall) UNINSTALL=1 ;;
    -h|--help) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
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
  rm -rf "$APP"   # the program and its downloaded add-ons
  rm -f "$BIN/uswap" "$ICON" "$DESKTOP" "$NAUTILUS" "$NEMO" "$DOLPHIN"
  remove_thunar
  info "done. FFmpeg and add-ons installed with your package manager were left installed."
  exit 0
fi

printf '\n%s  █  █ ▄▀▀▀▀%s    USwap installer\n' "$R" "$N"
printf '%s  █  █ ▀▀▀▀▄%s    %sno pip, no virtualenv%s\n' "$R" "$N" "$D" "$N"
printf '%s  ▀▄▄▀ ▄▄▄▄▀%s\n%s  ─────────►%s\n%s  ◄─────────%s\n\n' "$R" "$N" "$R" "$N" "$A" "$N"

# ------------------------------------------------------------ system packages
step "Checking Python and FFmpeg"
missing=()
have python3 && python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))' || missing+=(python3)
have ffmpeg || missing+=(ffmpeg)

if [ ${#missing[@]} -eq 0 ]; then
  info "both are already installed"
else
  if   have apt-get; then pm=apt;    cmd=(apt-get install -y)
  elif have dnf;     then pm=dnf;    cmd=(dnf install -y)
  elif have pacman;  then pm=pacman; cmd=(pacman -S --needed --noconfirm)
  elif have zypper;  then pm=zypper; cmd=(zypper --non-interactive install)
  else pm=""; fi
  pkgs=()
  for m in "${missing[@]}"; do
    case "$pm:$m" in
      pacman:python3) pkgs+=(python) ;;
      dnf:ffmpeg) pkgs+=(ffmpeg-free) ;;
      *) pkgs+=("$m") ;;
    esac
  done
  SUDO=""; [ "$(id -u)" = 0 ] || SUDO=sudo
  if [ -z "$pm" ]; then
    info "no known package manager. Install these yourself: ${missing[*]}"
  else
    answer=y
    if [ "$YES" = 0 ] && [ -t 0 ]; then
      read -r -p "  Install ${pkgs[*]} with $pm (needs sudo)? [Y/n] " answer || true
    fi
    case "${answer:-y}" in
      [nN]*) info "skipped" ;;
      *) [ "$pm" = apt ] && $SUDO apt-get update -qq || true
         if ! $SUDO "${cmd[@]}" "${pkgs[@]}"; then
           info "the package manager failed."
           [ "$pm" = pacman ] && info "on Arch/CachyOS/Manjaro, update first and retry:  sudo pacman -Syu"
         fi ;;
    esac
  fi
fi
have python3 || { echo "error: USwap needs Python 3.8 or newer." >&2; exit 1; }
have ffmpeg || info "FFmpeg is still missing: install it, or almost nothing will convert"

# ----------------------------------------------------------------- the program
step "Installing USwap"
mkdir -p "$APP" "$BIN" "$(dirname "$ICON")" "$(dirname "$DESKTOP")"
install -m 755 "$REPO/uswap.py" "$APP/uswap.py"
ln -sf "$APP/uswap.py" "$BIN/uswap"
cp "$REPO/assets/logo.png" "$ICON"
printf '%s\n' "$REPO" > "$APP/source"   # lets `uswap --update` use git pull
rm -f "$APP/open-in-terminal"           # leftover from 2.0
info "$("$APP/uswap.py" --version)  →  $BIN/uswap"

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
exec $RUN "\${files[@]}"
EOF
  chmod 755 "$NAUTILUS"
  info "Nautilus  →  right-click › Scripts › $LABEL"; found=1
fi
if have nemo; then
  mkdir -p "$(dirname "$NEMO")"
  printf '[Nemo Action]\nName=%s\nExec=%s %%F\nIcon-Name=uswap\nSelection=notnone\nExtensions=any;dir;\n' \
    "$LABEL" "$RUN" > "$NEMO"
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
Exec=$RUN %F
EOF
  chmod 755 "$DOLPHIN"
  info "Dolphin   →  right-click › $LABEL"; found=1
fi
if have thunar; then
  mkdir -p "$(dirname "$THUNAR")"
  remove_thunar
  block="<!-- uswap:begin -->
<action><icon>uswap</icon><name>$LABEL</name><unique-id>uswap-2</unique-id>
<command>$RUN %F</command><description>Convert with USwap</description><patterns>*</patterns>
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
info "try it:   uswap        (or right-click any file › $LABEL)"
info "more:     uswap › Optional formats   (documents, PDF, iPhone photos, Office)"
info "update:   uswap --update"
