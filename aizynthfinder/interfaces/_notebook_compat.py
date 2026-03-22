"""Compatibility helpers for notebook widgets.
"""

from __future__ import annotations

from typing import Any, Callable


try:
    import ipywidgets as widgets
    from IPython.display import HTML, display
    from ipywidgets import (
        BoundedIntText,
        Button,
        Checkbox,
        Dropdown,
        HBox,
        IntRangeSlider,
        IntSlider,
        IntText,
        Label,
        Output,
        SelectMultiple,
        Tab,
        Text,
        VBox,
    )

    HAS_IPYWIDGETS = True
except ImportError:
    HAS_IPYWIDGETS = False

    class HTML(str):
        """Fallback HTML wrapper."""

    def display(*_args: Any, **_kwargs: Any) -> None:
        """Fallback no-op display function."""

    class _Widget:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.children = list(args[0]) if args else []
            self.description = kwargs.get("description", "")
            self.style = kwargs.get("style", {})
            self.layout = kwargs.get("layout", {})
            self.disabled = kwargs.get("disabled", False)
            self.enabled = kwargs.get("enabled", True)
            self.continuous_update = kwargs.get("continuous_update", False)
            self.orientation = kwargs.get("orientation")
            self.readout = kwargs.get("readout", True)
            self.readout_format = kwargs.get("readout_format")
            self.rows = kwargs.get("rows")
            self.min = kwargs.get("min")
            self.max = kwargs.get("max")
            self.step = kwargs.get("step")
            self._value = kwargs.get("value")
            self._index = kwargs.get("index")
            self._observers: list[tuple[Callable[[dict[str, Any]], None], Any]] = []

        @property
        def value(self) -> Any:
            return self._value

        @value.setter
        def value(self, new_value: Any) -> None:
            old_value = self._value
            self._value = new_value
            self._notify("value", old_value, new_value)

        @property
        def index(self) -> Any:
            return self._index

        @index.setter
        def index(self, new_index: Any) -> None:
            old_index = self._index
            self._index = new_index
            self._notify("index", old_index, new_index)

        def observe(
            self, callback: Callable[[dict[str, Any]], None], names: Any = None
        ) -> None:
            self._observers.append((callback, names))

        def _notify(self, name: str, old: Any, new: Any) -> None:
            change = {"name": name, "old": old, "new": new, "owner": self}
            for callback, names in self._observers:
                if names is None or names == name or name in (names if isinstance(names, (list, tuple, set)) else []):
                    callback(change)

    class Output(_Widget):
        def clear_output(self) -> None:
            return None

        def __enter__(self) -> "Output":
            return self

        def __exit__(self, *_args: Any) -> bool:
            return False

    class Button(_Widget):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._click_handlers: list[Callable[[Any], None]] = []

        def on_click(self, callback: Callable[[Any], None]) -> None:
            self._click_handlers.append(callback)

    class Checkbox(_Widget):
        pass

    class Text(_Widget):
        pass

    class IntText(_Widget):
        pass

    class IntSlider(_Widget):
        pass

    class BoundedIntText(IntText):
        pass

    class IntRangeSlider(_Widget):
        pass

    class Label(_Widget):
        pass

    class HBox(_Widget):
        pass

    class VBox(_Widget):
        pass

    class SelectMultiple(_Widget):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.options = list(kwargs.get("options", []))
            self.value = tuple(kwargs.get("value", []))

    class Dropdown(_Widget):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._options: list[Any] = []
            super().__init__(*args, **kwargs)
            self.options = kwargs.get("options", [])
            if self._value is None and self._options:
                self._value = self._options[0]
            if self._index is None and self._options:
                try:
                    self._index = self._options.index(self._value)
                except ValueError:
                    self._index = 0

        @property
        def options(self) -> list[Any]:
            return self._options

        @options.setter
        def options(self, new_options: Any) -> None:
            self._options = list(new_options)
            if not self._options:
                self._index = None
                self._value = None
                return
            if self._value not in self._options:
                self._index = 0
                self._value = self._options[0]
            else:
                self._index = self._options.index(self._value)

        @_Widget.value.setter
        def value(self, new_value: Any) -> None:
            old_value = self._value
            self._value = new_value
            if new_value in self._options:
                self._index = self._options.index(new_value)
            self._notify("value", old_value, new_value)

        @_Widget.index.setter
        def index(self, new_index: Any) -> None:
            old_index = self._index
            self._index = new_index
            if new_index is None or new_index >= len(self._options):
                self._value = None
            else:
                self._value = self._options[new_index]
            self._notify("index", old_index, new_index)

    class Tab(_Widget):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.children = []
            self._titles: dict[int, str] = {}

        def set_title(self, index: int, title: str) -> None:
            self._titles[index] = title

    def link(source: tuple[Any, str], target: tuple[Any, str]) -> None:
        source_obj, source_name = source
        target_obj, target_name = target
        setattr(target_obj, target_name, getattr(source_obj, source_name))

    class _WidgetsNamespace:
        Checkbox = Checkbox
        Dropdown = Dropdown
        Button = Button
        Output = Output
        IntSlider = IntSlider
        link = staticmethod(link)

    widgets = _WidgetsNamespace()


__all__ = [
    "HAS_IPYWIDGETS",
    "HTML",
    "BoundedIntText",
    "Button",
    "Checkbox",
    "Dropdown",
    "HBox",
    "IntRangeSlider",
    "IntSlider",
    "IntText",
    "Label",
    "Output",
    "SelectMultiple",
    "Tab",
    "Text",
    "VBox",
    "display",
    "widgets",
]
