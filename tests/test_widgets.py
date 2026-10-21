from uswap.tui.widgets import Item, ListView, format_size


def items(*names):
    return [Item(n, n) for n in names]


def test_navigation_vim_and_arrows():
    lv = ListView(items("a", "b", "c"))
    lv.handle("j")
    lv.handle("down")
    assert lv.current().value == "c"
    lv.handle("down")  # clamped
    assert lv.current().value == "c"
    lv.handle("k")
    lv.handle("up")
    assert lv.current().value == "a"
    lv.handle("G")
    assert lv.current().value == "c"
    lv.handle("g")
    assert lv.current().value == "a"


def test_search_filters_and_esc_clears():
    lv = ListView(items("apple", "banana", "avocado"))
    lv.handle("/")
    assert lv.searching
    lv.handle("a")
    lv.handle("v")
    assert [i.value for _, i in lv.visible] == ["avocado"]
    lv.handle("enter")
    assert not lv.searching and lv.query == "av"
    assert lv.handle("esc") is None and lv.query == ""
    assert lv.handle("esc") == "cancel"


def test_search_accepts_spaces_and_backspace():
    lv = ListView(items("my file", "other"))
    lv.handle("/")
    for k in ("m", "y", "space", "f"):
        lv.handle(k)
    assert lv.query == "my f" and len(lv.visible) == 1
    lv.handle("backspace")
    assert lv.query == "my "


def test_multi_select_and_selectable():
    lv = ListView([Item("dir", selectable=False), Item("x", "x"), Item("y", "y")], multi=True)
    lv.handle("space")  # on a non-selectable item: ignored
    assert lv.selected == set()
    lv.handle("j")
    lv.handle("space")
    lv.handle("space")
    assert [i.value for i in lv.selected_items()] == ["x", "y"]


def test_enter_ignores_disabled():
    lv = ListView([Item("off", enabled=False), Item("on", "on")])
    assert lv.handle("enter") is None
    lv.handle("j")
    assert lv.handle("enter") == "enter"


def test_format_size():
    assert format_size(0) == "0 B"
    assert format_size(2048) == "2.0 KB"
    assert format_size(5 * 1024**2) == "5.0 MB"
