# data app script
import streamlit as st

from thematic_analysis_model.model.data_management import Manager, Loader
from thematic_analysis_model.controller.query_engine import QueryEngine

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
            st.write(query_engine.handle_input(search_input))

               
side_bar_fragment()
