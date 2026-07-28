# data app script
import streamlit as st
import random

from thematic_analysis_model.model.dataclasses import ModelOutput
from thematic_analysis_model.model.data_management import Manager, Loader
from thematic_analysis_model.controller.query_engine import QueryEngine
from thematic_analysis_model.view.data_for_widgets import ModelOutputSearchBarViewData
from thematic_analysis_model.view.widgets import model_search_view, model_main_view

import kaleido
kaleido.get_chrome_sync()

# session state management
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'current_model' not in st.session_state:
    st.session_state.current_model = None
if 'current_batch' not in st.session_state:
    st.session_state.current_batch = []
if 'active_mode' not in st.session_state:
    st.session_state.active_mode = None


# cacheing
@st.cache_resource
def get_utility_objs():
    loader = Loader()
    manager=Manager(loader=loader)
    query_engine = QueryEngine(manager=manager)
    return loader, manager, query_engine

loader, manager, query_engine = get_utility_objs()

# basic UI
# title + formatting
st.title('Model View')

# sidebar -> list db entries + search
#   requires sidebar context
@st.fragment
def side_bar_fragment():
    with st.sidebar:

        st.header("Search Database")
        with st.form(key='sidebar_form'):
            l_col, r_col = st.columns([3,2], vertical_alignment='center')
            with l_col:
                search_input= st.text_input(label='trial name: ', label_visibility='collapsed')
                check = st.checkbox(label='thumbnail', value=False)
            with r_col:
                button = st.form_submit_button('search')
        if button:
            search_results = query_engine.query_db(condition=query_engine.handle_input(text=search_input))
            st.session_state.search_results = search_results

        with st.container(height=500):
            for r in st.session_state.search_results:
                model_view_data = ModelOutputSearchBarViewData(
                    name=r.trial_config.trial_name,
                    batch=r.trial_config.batch_name,
                    id_=r.trial_config.id_,
                    topic_map=r.topic_map if check else None,
                    date=r.trial_config.date,
                    model_output=r
                )
                with model_search_view(model_view_data=model_view_data, id_=r.trial_config.id_, view_thumbnail=check):
                    pass

side_bar_fragment()


# main window
if st.session_state.active_mode == 'model_view':
    with model_main_view():
        pass
    
