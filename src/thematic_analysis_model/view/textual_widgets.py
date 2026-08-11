# widgets for terminal application
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Button, Label, Input, Collapsible
from textual.containers import VerticalGroup, HorizontalGroup, VerticalScroll, HorizontalScroll



# class for EntryFields
class EntryField(HorizontalGroup):
    def __init__(self, name: str, type_: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.entry_name = name
        self.type_ = type_

    def compose(self) -> ComposeResult:
        yield Label(self.entry_name, id=self.name)
        yield Input(id=self.entry_name, type=self.type_)

# class for Collapsible Entry Views
class CollapsibleEntryView(Widget):
    def __init__(self, name, entry_field_names: list[str], entry_field_types: list[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self.collapse_name = name
        self.entry_field_names = entry_field_names
        self.entry_field_types = entry_field_types

    def compose(self) -> ComposeResult:
        with Collapsible(title=self.collapse_name, collapsed=True):
            entries = [
                EntryField(
                    name=name,
                    type_=type_
                ) for name, type_ in zip(self.entry_field_names, self.entry_field_types, strict=True)
                ]
            yield from entries

# class for start button

# class for cancel button

# class for header command bar
class CommandBar(HorizontalScroll):
    def compose(self) -> ComposeResult:
        yield Button(label='Run Models', id='run-button', variant='success')
        yield Button(label='Cancel', id='cancel-button', variant='error')


# class for EntryView-> Hidden when modelling
#   when inputting parameters
class EntryView(VerticalScroll):
    def compose(self) -> ComposeResult:
        yield CollapsibleEntryView(
            name='General',
            entry_field_names=['test'],
            entry_field_types=['text']
                                   )
        yield CollapsibleEntryView(
            name='UMAP',
            entry_field_names=['test'],
            entry_field_types=['text']
                                   )
        yield CollapsibleEntryView(
            name='HDBSCAN',
            entry_field_names=['test'],
            entry_field_types=['text']
                                   )
    def hide_self(self) -> None:
        self.add_class('hidden')
    def show_self(self) -> None:
        self.remove_class('hidden')


# class for error logging 