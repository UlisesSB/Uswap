"""Dependency health check view (shared by `--doctor`, dashboard and settings)."""

from __future__ import annotations

from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from uswap.tui.theme import UI
from uswap.utils import system
from uswap.utils.i18n import t


def render_doctor(ui: UI) -> RenderableType:
    th, g = ui.theme, ui.g
    table = Table(box=None, show_header=True, header_style=f"bold {th.accent}", padding=(0, 2))
    table.add_column(t("doctor.col_name"), no_wrap=True)
    table.add_column(t("doctor.col_status"), no_wrap=True)
    table.add_column(t("doctor.col_for"), no_wrap=True)
    table.add_column(t("doctor.col_version"), style=th.dim, overflow="ellipsis", no_wrap=True)
    for dep in system.check_all():
        if dep.available:
            status = Text(f"{g.ok} {t('doctor.ok')}", style=th.ok)
        elif dep.required:
            status = Text(f"{g.fail} {t('doctor.missing')}", style=th.err)
        else:
            status = Text(f"{g.fail} {t('doctor.optional_missing')}", style=th.warn)
        table.add_row(dep.name, status, t(f"dep.{dep.purpose}"), dep.version)
    return table


def hints_for_missing() -> list[str]:
    """Install hints for missing optional binaries."""
    lines = []
    deps = {d.name: d for d in system.check_all()}
    missing = [n for n in ("ffmpeg", "pandoc", "pdftoppm") if not deps[n].available]
    if not missing:
        return lines
    if system.IS_WINDOWS:
        pkgs = {
            "ffmpeg": "Gyan.FFmpeg",
            "pandoc": "JohnMacFarlane.Pandoc",
            "pdftoppm": "poppler (scoop install poppler)",
        }
        for n in missing:
            lines.append(f"winget install {pkgs[n]}" if n != "pdftoppm" else pkgs[n])
    else:
        pkgs = {"ffmpeg": "ffmpeg", "pandoc": "pandoc", "pdftoppm": "poppler-utils"}
        lines.append(
            "sudo apt install " + " ".join(pkgs[n] for n in missing) + "   (Debian/Ubuntu)"
        )
        lines.append("sudo dnf install " + " ".join(pkgs[n] for n in missing) + "   (Fedora)")
        lines.append(
            "sudo pacman -S "
            + " ".join(pkgs[n] if n != "pdftoppm" else "poppler" for n in missing)
            + "   (Arch)"
        )
    return lines
