from thematic_analysis_model.model.dataclasses import validation_metric_adapter, ModelOutput, ValidationMetric, TrialConfig
from .data_for_widgets import ModelOutputSearchBarViewData

import streamlit as st
import pandas as pd
import kaleido
import contextlib


@contextlib.contextmanager
def model_search_view(model_view_data: ModelOutputSearchBarViewData, id_: str, view_thumbnail: bool = False):
    with st.container(border=True):
        if view_thumbnail is False:
            col_left, col_right = st.columns([3, 1], vertical_alignment='center')
            with col_left:
                st.markdown(f'### {model_view_data.name}')
                st.caption(f'batch: {model_view_data.batch} | date: {model_view_data.date} | id_: {model_view_data.id_}')
            with col_right:
                button = st.button(label='view', key=f'button_{id_}')
                if button:
                    set_model_state(model_view_data.model_output)
                    st.rerun(scope='app')
        else:
            col_left, col_middle, col_right = st.columns([3, 4, 2], vertical_alignment='center')
            with col_left:
                st.markdown(f'### {model_view_data.name}')
                st.caption(f'batch: {model_view_data.batch} | date: {model_view_data.date} | id_: {model_view_data.id_}')
            with col_middle:
                if model_view_data.topic_map:
                    fig = model_view_data.topic_map
                    fig.update_layout(
                        height=120,
                        width=90,
                        margin=dict(
                            l=0, r=0, t=0, b=0 
                        ),
                        font=dict(size=10),
                        showlegend=False,
                        xaxis=dict(visible=False),
                        yaxis=dict(visible=False)
                    )
                    pic = fig.to_image(
                        format='png',
                        width=400,
                        height=300,
                        scale=1.5
                    )
                    st.image(pic, use_container_width=True)
            with col_right:
                button = st.button(label='view', key=f'button_{id_}')
                if button:
                    set_model_state(model_view_data.model_output)
                    st.rerun(scope='app')

        yield

# load model from model search view
#   adds it to session state.
def set_model_state(model):
    st.session_state.current_model = model
    st.session_state.active_mode = 'model_view'

@contextlib.contextmanager
def model_main_view():
    model_output = st.session_state.current_model

    # config info
    trial_config = model_output.trial_config
    config_dict = trial_config.model_dump()
    st.dataframe(config_dict)



    # validation metric table
    validation_metrics = validation_metric_adapter.validate_json(model_output.validation_metrics)
    metric_dict = validation_metrics.model_dump()
    st.dataframe(metric_dict)

    # graphs


    yield
