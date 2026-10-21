# Usage guide

## Modes

| Command | Mode |
|---------|------|
| `uswap` | Dashboard (browse, batch, watch, settings, doctor) |
| `uswap FILE` | Quick pop-up for one file |
| `uswap FILE1 FILE2 ...` | Batch TUI with the files preselected |
| `uswap FILE... --to FMT` | Headless conversion |
| `uswap --watch DIR` | Hot-folder watcher |
| `uswap --config` | Settings panel |
| `uswap --doctor` / `--formats` / `--version` | Info commands |

Arguments may be files, folders (every file inside, non-recursive) or wildcards (`"*.png"`; quote them so your shell does not expand them on Linux, Windows shells never do).

## Quick pop-up

Shows the file name, detected type (from magic bytes), size, and the output formats available *with the tools you have installed*. Press `1`-`9` for an instant pick, or move with `j`/`k` and press `Enter`. On success the window closes after a short delay; on failure it stays open so you can read the error.

If the extension disagrees with the content (e.g. a PNG named `.jpg`) a warning is shown and the real type is used.

## Dashboard

* **Convert a file** - folder browser, then the pop-up.
* **Batch conversion** - multi-select browser, one target for all, parallel workers, per-file progress.
* **Watch a folder** - pick a folder, define rules, leave it running.
* **Settings** and **Dependency check**.

### Browser keys

`j`/`k` move, `l`/`Right` enter folder, `h`/`Left`/`Backspace` go up, `/` search, `.` hidden files, `~` home. In multi-select: `Space` toggle, `a` all supported files in the folder, `*` select by wildcard (type a pattern such as `*.png`), `Enter` confirm.

Selections persist while you navigate between folders.

## Headless mode

```bash
uswap photo.png --to webp
uswap "shots/*.png" --to jpg -o converted -j 8
uswap ~/Music --to mp3
```

Exit codes: `0` all converted, `1` at least one failure, `2` usage error (missing file, unknown format, no TTY for an interactive mode), `130` cancelled.

Files already in the target format are skipped.

## Naming and output location

Controlled from settings (`output.*`):

| Naming | Result for `a.png` to JPG |
|--------|---------------------------|
| keep | `a.jpg` |
| suffix | `a-converted.jpg` |
| overwrite | `a.jpg`, replacing an existing `a.jpg` |

Without *overwrite*, an existing name becomes `a (1).jpg`, `a (2).jpg`, ... The source file is never overwritten or deleted.

Location: same folder as the source, a custom folder, or `~/Downloads`. `-o DIR` overrides this for one run.

## Hot-folder watcher

```bash
uswap --watch ~/Downloads --rule heic:jpg --rule image:webp
```

A rule is `MATCH:TARGET` where `MATCH` is an extension (`heic`), a category (`image`, `audio`, `video`, `document`) or `*`. The first rule that applies and is possible wins. Without `--rule` the rules saved in the config are used (or you are asked to create one).

Behavior worth knowing:

* Files still being written (downloads, copies) are waited for until their size is stable.
* Temporary names (`.part`, `.crdownload`, `.tmp`, dotfiles) are ignored.
* Files created by USwap itself are never converted again, so rules cannot loop.
* Existing files are not touched; only files that appear while watching.

Keys: `p` pause/resume, `q` stop.

## Notes on formats

* Video to GIF uses 12 fps and 480 px width. Video to an audio format extracts the audio track.
* JPG/BMP/PDF output flatten transparency over white.
* Animated GIF/WebP keep their frames when converted between each other.
* PDF to PNG/JPG renders at 150 dpi; multi-page PDFs produce `name-1.png`, `name-2.png`, ...
* Text files named with a binary extension (e.g. text in `x.png`) are rejected as unsupported.
