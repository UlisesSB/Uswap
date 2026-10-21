# Configuration

Location:

* Linux/macOS: `$XDG_CONFIG_HOME/uswap/config.json` (default `~/.config/uswap/config.json`)
* Windows: `%APPDATA%\uswap\config.json`
* Override the folder with the `USWAP_CONFIG_DIR` environment variable.

Edit it from `uswap --config`, or by hand. Missing keys fall back to defaults and unknown keys are preserved. A corrupt file is renamed to `config.json.bak` and defaults are used.

## Reference

| Key | Values | Default | Meaning |
|-----|--------|---------|---------|
| `language` | `auto`, `en`, `es` | `auto` | UI language (`auto` follows `USWAP_LANG`, `LC_ALL`, `LANG`) |
| `theme` | `gruvbox`, `nord`, `catppuccin`, `tokyo-night`, `monokai` | `gruvbox` | Color scheme |
| `glyphs` | `unicode`, `ascii` | `unicode` | Use `ascii` on legacy terminals |
| `output.mode` | `same`, `custom`, `downloads` | `same` | Where results are written |
| `output.custom_dir` | path | `""` | Used when mode is `custom` (`~` allowed) |
| `output.naming` | `keep`, `suffix`, `overwrite` | `keep` | See [USAGE](USAGE.md#naming-and-output-location) |
| `output.suffix` | text | `-converted` | Suffix for `suffix` naming |
| `quality.image` | 1-100 | `90` | JPG and WebP quality |
| `batch.workers` | 1-32 | `4` | Parallel conversions |
| `quick_popup.auto_close` | bool | `true` | Close the pop-up after success |
| `quick_popup.close_delay` | seconds | `0.8` | Delay before closing |
| `watcher.recursive` | bool | `false` | Watch sub-folders too |
| `watcher.rules` | list | `[]` | `[{"match": "png", "target": "webp"}]` |

## Example

```json
{
  "language": "es",
  "theme": "tokyo-night",
  "output": { "mode": "custom", "custom_dir": "~/Converted", "naming": "suffix" },
  "watcher": { "rules": [ { "match": "heic", "target": "jpg" } ] }
}
```

## Environment variables

| Variable | Effect |
|----------|--------|
| `USWAP_CONFIG_DIR` | Use another configuration folder |
| `USWAP_LANG` | Force the language when `language` is `auto` |
| `TERMINAL` | Terminal emulator used by the Linux context-menu launcher |
