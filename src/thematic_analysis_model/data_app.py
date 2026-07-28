# data app script
import streamlit as st

from thematic_analysis_model.model.data_management import Manager, Loader
from thematic_analysis_model.controller.query_engine import QueryEngine
from thematic_analysis_model.view.data_for_widgets import ModelOutputViewData

# session state management

# cacheing
loader = Loader()
manager=Manager(loader=loader)
query_engine = QueryEngine(manager=manager)

# basic UI
# title + formatting
st.title('hello world')

# sidebar -> list db entries + search
#   requires sidebar context
@st.fragment
def side_bar_fragment():
    with st.sidebar:
        st.header("Search Database")
        with st.form(key='sidebar_form'):
            search_input= st.text_input(label='trial name: ', label_visibility='collapsed')
            button = st.form_submit_button('search')
        if button:
            search_results = query_engine.query_db(condition=query_engine.handle_input(text=search_input))
        else:
            search_results = []
        with st.container(height=500):
            for i in range(20):
                st.checkbox(label=str(i))



side_bar_fragment()
