from thematic_analysis_model.model.dataclasses import validation_metric_adapter, ModelOutput, ValidationMetric, TrialConfig
from thematic_analysis_model.model.data_management import Manager
from thematic_analysis_model.model.validating import StabilityEvaluator
from .data_for_widgets import ModelOutputSearchBarViewData

import streamlit as st
import json
from plotly.io import from_json
import plotly.express as plx
import pandas as pd
import kaleido
import contextlib
from dataclasses import fields
from collections import defaultdict


@contextlib.contextmanager
def model_search_view(model_view_data: ModelOutputSearchBarViewData, id_: str, view_thumbnail: bool = False):
    with st.container(border=True):
        if view_thumbnail is False:
            col_left, col_right = st.columns([3, 1], vertical_alignment='center')
            with col_left:
                st.markdown(f'### {model_view_data.name}')
                st.caption(f'batch: {model_view_data.batch} | date: {model_view_data.date} | id_: {model_view_data.id_}')
            with col_right:
                model_button = st.button(label='model', key=f'model_button_{id_}')

                if model_button:
                    set_model_state(model_view_data.model_output)
                    st.rerun(scope='app')

                batch_button = st.button(label='batch', key=f'batch_button{id_}')
                if batch_button:
                    set_batch_state(batch_name=str(model_view_data.batch))
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

# load batch from batch_search view
#   adds batch of models to session state
#   change active state to batch_view
def set_batch_state(batch_name: str):
    st.session_state.current_batch_name = batch_name
    st.session_state.active_mode = 'batch_view'

@contextlib.contextmanager
def model_main_view():
    model_output = st.session_state.current_model

    # basic ui
    st.title('Model View')

    # config info
    trial_config = model_output.trial_config
    config_dict = trial_config.model_dump()
    st.dataframe(config_dict)

    # validation metric table
    validation_metrics = validation_metric_adapter.validate_json(model_output.validation_metrics)
    metric_dict = validation_metrics.model_dump()
    st.dataframe(metric_dict)

    # graphs
    topic_map = from_json(model_output.topic_map, engine='json') if model_output.topic_map else None
    if topic_map:
        st.plotly_chart(topic_map)

    doc_map = from_json(model_output.document_map, engine='json') if model_output.document_map else None
    if doc_map:
        st.plotly_chart(doc_map)

    heatmap = from_json(model_output.heatmap, engine='json') if model_output.heatmap else None
    if heatmap:
        st.plotly_chart(heatmap)

    hierarchy_map = from_json(model_output.hierarchy_map, engine='json') if model_output.hierarchy_map else None
    if hierarchy_map:
        st.plotly_chart(hierarchy_map)

    yield

@contextlib.contextmanager
def batch_main_view(manager: Manager, stability_evaluator: StabilityEvaluator):
    # load model outputs
    batch: list[ModelOutput] = manager.get_model_output(
        condition=f'trial_config.batch_name = "{st.session_state.current_batch_name}"'
    )

    # basic ui
    st.title('Batch View')

    # get batch info
    #   num batches
    #   individual trials + configs


    # get stability metrics
    stability_metric_data = stability_evaluator.evaluate(
        batch_name=st.session_state.current_batch_name
    )
    render_nested_dict(d=stability_metric_data)

    # if incrementing batch -> specific view
    # elif non-incrementing batch -> diff view
    # view validation metric statistics
    batch_increment_button = st.button(label='Batch Increments', key='ajhdjsahdajsndf')
    if batch_increment_button:
        incrementing_param = find_incrementing_parameter(batch=batch)

        st.write(len(incrementing_param))

        charts = []
        for param in incrementing_param:
            df = load_line_chart_data(batch=batch, param=param)

            for col in df.columns:
                if col in [param, 'topics_pairwise_distance', 'redundant_pairs', 'prob_distributions']:
                    continue

                chart = plx.line(data_frame=df[[param, col]], x=param, y=col, title=f'{col} over {param}')
                charts.append(chart)


        for chart in charts:
            st.plotly_chart(chart)
    
    yield

# render nested dicts cleanly
def render_nested_dict(d, level=0):
    for key, val in d.items():
        clean_key = key.replace('_', ' ').title()
        if isinstance(val, dict):
            with st.expander(f"**{clean_key}**", expanded=True):
                render_nested_dict(val, level + 1)
        else:
            formatted_val = f"{val:.4f}" if isinstance(val, float) else val
            st.text(f"{clean_key}: {formatted_val}")
            

# identify parameter that increments
def find_incrementing_parameter(batch: list[ModelOutput]):
    trial_configs: list[TrialConfig] = [
        model_output.trial_config for model_output in batch
    ]

    attribute_dict = defaultdict(list)
    for config in trial_configs:
        for attr_name, attr_info in type(config).model_fields.items():
            # filter unwanted attributes
            if attr_name in ['trial_name', 'trial_num', 'id_', 'model_save_path']: continue
            if attr_info.annotation is str: continue

            # append to attribute dict
            attribute_dict[attr_name].append(getattr(config, attr_name))
    attribute_dict = dict(attribute_dict)

    # check for incrementing values
    incrementing_fields = []
    for attr in attribute_dict.keys():
        if len(set(attribute_dict[attr])) > 1:
            incrementing_fields.append(attr)
    
    return incrementing_fields

# load data needed for line chart -> based on parameter that is incremented
def load_line_chart_data(batch: list[ModelOutput], param: str) -> pd.DataFrame:
    configs = [model_output.trial_config for model_output in batch]
    validation_metrics = [validation_metric_adapter.validate_json(model_output.validation_metrics) for model_output in batch]

    # get values of parameter that is incrementing in order of batch
    relevant_param_values = []
    for config in configs:
        for attr_name, attr_info in type(config).model_fields.items():
            if attr_name == param:
                relevant_param_values.append(getattr(config, attr_name))

    # get values of other data that is incrementing in order of batch
    data_dict = defaultdict(list)
    for metric in validation_metrics:
        for attr_name, attr_info in type(metric).model_fields.items():
            data_dict[attr_name].append(getattr(metric, attr_name))
    data_dict[param] = relevant_param_values

    df = pd.DataFrame(data_dict).sort_values(by=param)

    # Group repeating parameter values and compute the mean of metrics
    df = df.groupby(param, as_index=False).mean(numeric_only=True)

    return df

    

    ...