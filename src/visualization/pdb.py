#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc
import dash_bio as dashbio
from dash import dcc, html
import plotly.graph_objects as go

from .base import *


representation_options = [
    {"label": "backbone", "value": "backbone"},
    {"label": "ball+stick", "value": "ball+stick"},
    {"label": "cartoon", "value": "cartoon"},
    {"label": "hyperball", "value": "hyperball"},
    {"label": "licorice", "value": "licorice"},
    {"label": "axes+box", "value": "axes+box"},
    {"label": "helixorient", "value": "helixorient"},
]


def init_app_pdb(
    original_id_col: list, umap_paras: dict, csv_header: list[str], fig: go.Figure
):
    """
    Initializes app & Builds html layout for Dash
    :return: layout
    """
    app = get_app()

    app.layout = dbc.Container(
        [
            # Header
            get_header(app),
            # sizing of the molecule viewer
            dcc.Location(id="url"),
            html.Div(id="molviewer_sizing_div", hidden=True),
            # storage to save the selected molecules
            # Needed for image download name
            dcc.Store(id="mol_name_storage"),
            # Storage to save the clicked on molecule in the graph,
            # needed for replacing the clicked molecule in the list
            dcc.Store(id="clicked_mol_storage"),
            # Toast that is displayed if a html file is created
            get_download_toast(),
            # Toast to display info on selected protein
            get_info_toast(),
            # graph and controls
            dbc.Row(
                [
                    dbc.Col(
                        get_graph_container(umap_paras, True, csv_header, fig),
                        id="left_col",
                        width=6,
                        style={"border-right": "solid black 1px"},
                    ),
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dcc.Markdown(
                                                "Molecules:",
                                                style={
                                                    "margin-top": "20px",
                                                    "margin-bottom": "0px",
                                                    "padding-top": "0px",
                                                    "padding-bottom": "0px",
                                                    "height": "30px",
                                                },
                                            ),
                                        ],
                                        xxl=9,
                                        xl=8,
                                        lg=7,
                                        md=6,
                                        sm=5,
                                        xs=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Stack(
                                                direction="horizontal",
                                                children=[
                                                    dbc.Button(
                                                        "",
                                                        id="reset_view_button",
                                                        class_name="bi bi-arrow-counterclockwise",
                                                        color="dark",
                                                        outline=True,
                                                        style={
                                                            "margin-top": "5px",
                                                            "margin-bottom": "5px",
                                                            "margin-right": "20px",
                                                        },
                                                    ),
                                                    dbc.Button(
                                                        "",
                                                        id="molecules_settings_button",
                                                        class_name="bi bi-gear-wide-connected",
                                                        outline=True,
                                                        color="dark",
                                                        style={
                                                            "margin-top": "5px",
                                                            "margin-bottom": "5px",
                                                        },
                                                    ),
                                                ],
                                            ),
                                        ],
                                        xxl=3,
                                        xl=4,
                                        lg=5,
                                        md=6,
                                        sm=7,
                                        xs=8,
                                    ),
                                ]
                            ),
                            dcc.Dropdown(
                                id="molecules_dropdown",
                                options=original_id_col,
                                multi=True,
                                style={"margin-bottom": "5px"},
                            ),
                            html.Div(
                                [
                                    dashbio.NglMoleculeViewer(
                                        id="ngl_molecule_viewer",
                                    ),
                                ],
                                id="moleculeviewer_div",
                                style={
                                    "border-bottom": "1px solid grey",
                                    "border-right": "1px solid grey",
                                    "margin-left": "0px",
                                },
                            ),
                            dbc.Offcanvas(
                                id="molecules_offcanvas",
                                title="Settings",
                                is_open=False,
                                children=[
                                    dcc.Markdown("Representations:"),
                                    dcc.Dropdown(
                                        id="representation_dropdown",
                                        options=representation_options,
                                        multi=True,
                                        value=["cartoon"],
                                    ),
                                    html.Br(),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dcc.Markdown("Start:"),
                                                    dcc.Dropdown(
                                                        id="range_start",
                                                        disabled=True,
                                                    ),
                                                ]
                                            ),
                                            dbc.Col(
                                                [
                                                    dcc.Markdown("End:"),
                                                    dcc.Dropdown(
                                                        id="range_end",
                                                        disabled=True,
                                                    ),
                                                ]
                                            ),
                                            dbc.Col(
                                                [
                                                    dcc.Markdown(
                                                        "Highlighted atoms:",
                                                    ),
                                                    dcc.Dropdown(
                                                        id="selected_atoms",
                                                        multi=True,
                                                        disabled=True,
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                    html.Br(),
                                    dcc.Markdown("Spacing:"),
                                    dcc.Slider(
                                        id="spacing_slider",
                                        min=10,
                                        max=200,
                                        value=50,
                                        marks=None,
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": False,
                                        },
                                    ),
                                    dcc.Markdown("Space distribution:"),
                                    dcc.Slider(
                                        id="distribution_slider",
                                        min=3,
                                        max=9,
                                        value=6,
                                        step=1,
                                        marks=None,
                                    ),
                                    dbc.Button(
                                        "Recalculate molecule viewing size",
                                        id="recal_size_button",
                                        class_name="d-grid mx-auto",
                                        color="dark",
                                        outline=True,
                                        style={"margin-bottom": "10px"},
                                    ),
                                    dcc.Markdown("Height:"),
                                    dcc.Slider(
                                        id="height_slider",
                                        min=200,
                                        max=5000,
                                        value=300,
                                        marks=None,
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": False,
                                        },
                                    ),
                                    dcc.Markdown("Width:"),
                                    dcc.Slider(
                                        id="width_slider",
                                        min=200,
                                        max=5000,
                                        value=500,
                                        marks=None,
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": False,
                                        },
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dcc.Input(
                                                    id="filename_input",
                                                    type="text",
                                                    placeholder="filename",
                                                    style={
                                                        "height": "38px",
                                                        "margin-right": "20px",
                                                    },
                                                ),
                                                width=6,
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    "Download image",
                                                    id="download_molecule_button",
                                                    color="dark",
                                                    outline=True,
                                                    disabled=True,
                                                ),
                                                width=6,
                                            ),
                                        ]
                                    ),
                                ],
                                style={"width": "50%"},
                            ),
                        ],
                        id="right_col",
                        width=6,
                    ),
                ]
            ),
            # modal with disclaimer that opens on startup
            # has to be at the end, otherwise automatic sizing doesn't work...
            get_disclaimer_modal(),
        ],
        fluid=True,
    )

    return app
