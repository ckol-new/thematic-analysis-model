# class for terminal application
from textual.app import App, ComposeResult
from textual.widgets import Header, Button
from thematic_analysis_model.view.textual_widgets import *

from pathlib import Path

# main app\
class TerminalApp(App):
    BINDINGS = [
        
    ]
    CSS_PATH = Path('/Users/christopher.kollar/research/HealthyCityLab/DementiaForumAnalysis/thematic-analysis-model/src/thematic_analysis_model/view/textual_styling.tcss')
    def compose(self) -> ComposeResult:
        with VerticalGroup():
            yield Header("Terminal App")
            yield CommandBar()
            yield EntryView()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id 
        if button_id == 'run-button': 
            self.query_one(EntryView).hide_self()
            self.query_one('#run-button').disabled = True
            self.query_one('#cancel-button').disabled = False
        elif button_id == 'cancel-button':
            self.query_one(EntryView).show_self()
            self.query_one('#run-button').disabled = False 
            self.query_one('#cancel-button').disabled = True

app = TerminalApp()
app.run()

