#!/usr/bin/env bash
# USwap - one-step installer for Linux
#
#   git clone https://github.com/YOUR-USER/uswap.git && cd uswap && ./install.sh
#
# What it does (per-user, sudo only for system packages):
#   1. installs FFmpeg, Pandoc and Poppler with your package manager (asks first)
#   2. creates a private virtualenv in ~/.local/share/uswap and installs USwap
#   3. links the `uswap` command into ~/.local/bin
#   4. adds "Convert with USwap" to your file manager's right-click menu
#
# Options:
#   -y, --yes            do not ask questions (install system packages with sudo)
#   --no-system-deps     skip FFmpeg/Pandoc/Poppler (images only)
#   --no-menus           skip the right-click menu entries
#   --uninstall          remove USwap, its venv and the menu entries
#   -h, --help           show this help
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/uswap"
VENV="$APP_HOME/venv"
BIN_DIR="$HOME/.local/bin"

ASSUME_YES=0; SYSTEM_DEPS=1; MENUS=1; UNINSTALL=0
for arg in "$@"; do
  case "$arg" in
    -y|--yes) ASSUME_YES=1 ;;
    --no-system-deps) SYSTEM_DEPS=0 ;;
    --no-menus) MENUS=0 ;;
    --uninstall) UNINSTALL=1 ;;
    -h|--help) sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $arg (try --help)" >&2; exit 2 ;;
  esac
done

if [ -t 1 ]; then RED=$'\033[1;31m'; DIM=$'\033[2m'; RST=$'\033[0m'; else RED=""; DIM=""; RST=""; fi
step() { printf '%s==>%s %s\n' "$RED" "$RST" "$*"; }
info() { printf '    %s\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

ask() {  # ask "question" -> 0 for yes
  [ "$ASSUME_YES" = 1 ] && return 0
  [ -t 0 ] || return 1
  local reply; read -r -p "    $1 [Y/n] " reply
  case "$reply" in ""|y|Y|yes|YES|s|S|si|SI) return 0 ;; *) return 1 ;; esac
}

# ---------------------------------------------------------------- uninstall
if [ "$UNINSTALL" = 1 ]; then
  step "Removing USwap"
  [ -x "$REPO_DIR/scripts/menu-linux.sh" ] && "$REPO_DIR/scripts/menu-linux.sh" --uninstall || true
  rm -f "$BIN_DIR/uswap"
  rm -rf "$APP_HOME"
  info "done. Your settings (~/.config/uswap) were kept; system packages were not touched."
  exit 0
fi

# ------------------------------------------------------------------- python
step "Checking Python"
PM=""
for c in apt-get dnf pacman zypper; do have "$c" && { PM="$c"; break; }; done

pkg_install() {  # pkg_install <apt> <dnf> <pacman> <zypper>
  [ -n "$PM" ] || return 1
  case "$PM" in
    apt-get) sudo apt-get update -qq && sudo apt-get install -y $1 ;;
    dnf)     sudo dnf install -y $2 ;;
    pacman)  sudo pacman -S --needed --noconfirm $3 ;;
    zypper)  sudo zypper --non-interactive install $4 ;;
  esac
}

PYTHON=""
for c in python3.13 python3.12 python3.11 python3.10 python3; do
  if have "$c" && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PYTHON="$(command -v "$c")"; break
  fi
done
if [ -z "$PYTHON" ]; then
  info "Python 3.10+ not found."
  if ask "Install Python with your package manager (sudo)?"; then
    pkg_install "python3 python3-venv" "python3" "python" "python3" || true
    have python3 && PYTHON="$(command -v python3)"
  fi
fi
[ -n "$PYTHON" ] || { echo "error: Python 3.10 or newer is required." >&2; exit 1; }
info "using $("$PYTHON" --version) at $PYTHON"

if ! "$PYTHON" -c 'import venv, ensurepip' 2>/dev/null; then
  info "The 'venv' module is missing."
  if ask "Install python3-venv (sudo)?"; then
    pkg_install "python3-venv" "python3" "python" "python3" || true
  fi
  "$PYTHON" -c 'import venv, ensurepip' 2>/dev/null || { echo "error: python venv/ensurepip unavailable." >&2; exit 1; }
fi

# -------------------------------------------------------------- system deps
if [ "$SYSTEM_DEPS" = 1 ]; then
  step "Checking FFmpeg, Pandoc and Poppler"
  missing=()
  have ffmpeg   || missing+=(ffmpeg)
  have pandoc   || missing+=(pandoc)
  have pdftoppm || missing+=(poppler)
  if [ ${#missing[@]} -eq 0 ]; then
    info "all present"
  elif [ -z "$PM" ]; then
    info "no supported package manager found; please install: ${missing[*]}"
  elif ask "Install ${missing[*]} with $PM (needs sudo)?"; then
    apt="" dnf="" pac="" zyp=""
    for m in "${missing[@]}"; do
      case "$m" in
        ffmpeg) apt+=" ffmpeg"; dnf+=" ffmpeg-free"; pac+=" ffmpeg"; zyp+=" ffmpeg" ;;
        pandoc) apt+=" pandoc"; dnf+=" pandoc"; pac+=" pandoc-cli"; zyp+=" pandoc" ;;
        poppler) apt+=" poppler-utils"; dnf+=" poppler-utils"; pac+=" poppler"; zyp+=" poppler-tools" ;;
      esac
    done
    pkg_install "$apt" "$dnf" "$pac" "$zyp" || info "some packages failed to install; run 'uswap --doctor' later."
  else
    info "skipped. Only images will work until you install: ${missing[*]}"
  fi
fi

# -------------------------------------------------------------------- venv
step "Installing USwap"
mkdir -p "$APP_HOME" "$BIN_DIR"
[ -x "$VENV/bin/python" ] || "$PYTHON" -m venv "$VENV"
"$VENV/bin/python" -m pip install --quiet --upgrade pip
"$VENV/bin/python" -m pip install --quiet --upgrade "$REPO_DIR"
ln -sf "$VENV/bin/uswap" "$BIN_DIR/uswap"
info "installed $("$BIN_DIR/uswap" --version) -> $BIN_DIR/uswap"

# ------------------------------------------------------------------- menus
if [ "$MENUS" = 1 ]; then
  step "Adding the right-click menu entry"
  PATH="$BIN_DIR:$PATH" "$REPO_DIR/scripts/menu-linux.sh"
fi

# -------------------------------------------------------------------- done
echo
step "Done"
"$BIN_DIR/uswap" --doctor || true
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo
     info "$BIN_DIR is not in your PATH. Add this to ~/.bashrc or ~/.zshrc:"
     info "    export PATH=\"\$HOME/.local/bin:\$PATH\""
     ;;
esac
info "Try it:  uswap      (or right-click a file > Convert with USwap)"
