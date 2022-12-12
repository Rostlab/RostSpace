#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from visualization import Visualizator
from preprocessing import StructureContainer

from pathlib import Path
from dash import Input, Output
from dash.exceptions import PreventUpdate
import dash
import dash_bio.utils.ngl_parser as ngl_parser
import pandas as pd

from pandas import DataFrame


def to_mapped_id(sel_original_seq_ids: list, original_id_col: list, df: DataFrame):
    seq_ids = list()

    for id in sel_original_seq_ids:
        index_num = original_id_col.index(id)
        mapped_id = df.index[index_num]
        seq_ids.append(mapped_id)

    return seq_ids


def to_original_id(sel_mapped_seq_ids: list, original_id_col: list, df: DataFrame):
    seq_ids = list()

    for id in sel_mapped_seq_ids:
        index_num = df.index.get_indexer_for([id])[0]
        original_id = original_id_col[index_num]
        seq_ids.append(original_id)

    return seq_ids


def handle_highlighting(
    seq_ids: list,
    struct_container: StructureContainer,
    range_start: int,
    range_end: int,
    selected_atoms: list,
):
    # disable range and highlighting selection in case more than 1 atom is selected
    start_disabled = False
    end_disabled = False
    atoms_disabled = False

    range_for_start = list()
    range_for_end = list()
    selectable_atoms = list()

    if len(seq_ids) > 1 or len(seq_ids) == 0:
        # disable the dropdown menus for range selection and highlighting if more than 1 molecule is selected
        start_disabled = True
        end_disabled = True
        atoms_disabled = True

    # only one molecule selected
    else:
        molecule_range, strand = struct_container.get_range(seq_ids[0])
        range_for_start = molecule_range
        range_for_end = molecule_range
        selectable_atoms = molecule_range

        # start of range selected
        if range_start is not None:
            # reset values
            range_for_end = []

            # remove numbers below for selection of end of range
            for num in molecule_range:
                if num > range_start:
                    range_for_end.append(num)

            # set selectable atoms accordingly
            selectable_atoms = range_for_end

        # end of range selected
        if range_end is not None:
            # reset values
            range_for_start = []

            # remove numbers above for selection of start of range
            for num in molecule_range:
                if num < range_end:
                    range_for_start.append(num)

            # set selectable atoms accordingly
            selectable_atoms = range_for_start

        # both, start and end selected
        if range_start is not None and range_end is not None:
            # reset values
            selectable_atoms = []

            for num in molecule_range:
                if range_start <= num <= range_end:
                    selectable_atoms.append(num)

            # remove selected atom if not in range of selectable atoms
            if selected_atoms is not None:
                for atom in selected_atoms:
                    if atom not in selectable_atoms:
                        selected_atoms.remove(atom)

        # seq id has to be edited if range start and end are selected
        seq_id = seq_ids[0]
        strand_set = False

        # append the range selection to the seq id accordingly
        if range_start is not None and range_end is not None:
            # append strand to seq id string
            seq_id = seq_id + f".{strand}"
            strand_set = True

            seq_id = seq_id + f":{range_start}-{range_end}"

        # append selected atoms to the string accordingly
        if selected_atoms is not None:
            if len(selected_atoms) > 0:
                if not strand_set:
                    # append strand to seq id string
                    seq_id = seq_id + f".{strand}"

                # bring selected atoms into string format comma separated
                atoms = ""
                for atom in selected_atoms:
                    atoms = atoms + f"{atom},"

                # remove last comma
                atoms = atoms[:-1]

                seq_id = seq_id + f"@{atoms}"

        # replace seq id with new edited seq id
        seq_ids[0] = seq_id

    return (
        start_disabled,
        end_disabled,
        atoms_disabled,
        range_for_start,
        range_for_end,
        selectable_atoms,
    )


def get_callbacks_pdb(app, df, struct_container, original_id_col):
    @app.callback(
        Output("ngl_molecule_viewer", "data"),
        Output("molecules_dropdown", "value"),
        Output("range_start", "disabled"),
        Output("range_end", "disabled"),
        Output("selected_atoms", "disabled"),
        Output("range_start", "options"),
        Output("range_end", "options"),
        Output("selected_atoms", "options"),
        Output("selected_atoms", "value"),
        Output("download_molecule_button", "disabled"),
        Output("mol_name_storage", "data"),
        Input("graph", "clickData"),
        Input("molecules_dropdown", "value"),
        Input("range_start", "value"),
        Input("range_end", "value"),
        Input("selected_atoms", "value"),
        Input("reset_view_button", "n_clicks"),
    )
    def display_molecule(
        clickdata,
        dd_molecules: list,
        range_start: int,
        range_end: int,
        selected_atoms: list,
        reset_view_clicks: int,
    ):
        """
        callback function to handle the displaying of the molecule
        :param clickdata: given data by clicking on a datapoint in the 3D plot
        :param dd_molecules: selected molecules in the dropdown menu
        :param range_start: in the dropdown menu selected start
        :param range_end: in the dropdown menu selected end
        :param selected_atoms: selected values of the dropdown menu for highlighted atoms
        :param reset_view_clicks: button to reset the view of the molecule viewer.
        :return:
        """

        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # convert original to mapped IDs
        seq_ids = list()
        saved_seq_ids = list()
        if dd_molecules is not None:
            if original_id_col is not None:
                seq_ids = to_mapped_id(dd_molecules, original_id_col, df)
            else:
                seq_ids = dd_molecules

            # save unedited seq ids to replace edited seq ids later
            # (editing for range selection and highlighting)
            saved_seq_ids = list(seq_ids)

        # triggered by click on graph
        if ctx.triggered_id == "graph":
            # dict with data of clickdata
            points = clickdata["points"][0]
            # class_index value and it's index number
            index_num = int(points["pointNumber"])
            class_index = points["curveNumber"]

            # extract df_row of selected protein
            class_df = df[df["class_index"] == class_index]
            df_row = class_df.iloc[index_num]
            # add missing name to series
            name = pd.Series(class_df.index[index_num])
            name.index = ["Name"]
            df_row = pd.concat([name, df_row])

            # extract sequence ID
            seq_id = df_row["Name"]

            if seq_id not in seq_ids:
                # add selected sequence ID to already selected IDs
                seq_ids.append(seq_id)

        # path to .pdb file
        struct_path = str(struct_container.get_structure_dir()) + "/"

        # handle the range and atom selection
        (
            start_disabled,
            end_disabled,
            atoms_disabled,
            range_for_start,
            range_for_end,
            selectable_atoms,
        ) = handle_highlighting(
            seq_ids, struct_container, range_start, range_end, selected_atoms
        )

        # data format for molecule viewer
        data_list = [
            ngl_parser.get_data(
                data_path=struct_path,
                pdb_id=seq_id,
                color="black",
                reset_view=True,
                local=True,
            )
            for seq_id in seq_ids
        ]

        if ctx.triggered_id != "graph":
            # replace edited seq ids with saved unedited seq ids
            seq_ids = saved_seq_ids

        if original_id_col is not None:
            # back to original IDs
            seq_ids = to_original_id(seq_ids, original_id_col, df)

        # enable download button at first protein selection
        download_disabled = False

        # convert sequence ids list into string format
        mol_names = "_".join(seq_ids)

        # prevent updating if data list is empty since molecule viewer gives error otherwise
        if not data_list:
            raise PreventUpdate

        return (
            data_list,
            seq_ids,
            start_disabled,
            end_disabled,
            atoms_disabled,
            range_for_start,
            range_for_end,
            selectable_atoms,
            selected_atoms,
            download_disabled,
            mol_names,
        )

    @app.callback(
        Output("ngl_molecule_viewer", "molStyles"),
        Input("representation_dropdown", "value"),
        Input("spacing_slider", "value"),
    )
    def set_mol_style(selected_representation, spacing_slider_value):
        molstyles_dict = {
            "representations": selected_representation,
            "chosenAtomsColor": "white",
            "chosenAtomsRadius": 0.5,
            "molSpacingXaxis": spacing_slider_value,
            "sideByside": True,
        }

        return molstyles_dict

    @app.callback(
        Output("molecules_offcanvas", "is_open"),
        Input("molecules_settings_button", "n_clicks"),
    )
    def handle_molecules_canvas(button_click):
        if button_click:
            return True

    # molecule viewer sizing
    app.clientside_callback(
        """
        function(href) {
            var w = window.innerWidth;
            var h = window.innerHeight;
            return [h, w];
        }
        """,
        Output("molviewer_sizing_div", "children"),
        Input("url", "href"),
        Input("recal_size_button", "n_clicks"),
    )

    @app.callback(
        Output("ngl_molecule_viewer", "height"),
        Output("ngl_molecule_viewer", "width"),
        Output("height_slider", "value"),
        Output("width_slider", "value"),
        Output("moleculeviewer_div", "style"),
        Input("molviewer_sizing_div", "children"),
        Input("height_slider", "value"),
        Input("width_slider", "value"),
        Input("moleculeviewer_div", "style"),
        Input("distribution_slider", "value"),
    )
    def set_molviewer_size(
        sizing, slider_height, slider_width, div_style_dic, distribution
    ):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # sliders are used
        if ctx.triggered_id == "height_slider" or ctx.triggered_id == "width_slider":
            # set style of div accordingly
            div_style_dic["height"] = str(slider_height + 1) + "px"
            div_style_dic["width"] = str(slider_width + 1) + "px"

            return (
                slider_height,
                slider_width,
                slider_height,
                slider_width,
                div_style_dic,
            )

        # automatic sizing
        height = (sizing[0] - 150) / 1.05
        width = sizing[1] / 2.1

        # fit sizing to distribution
        if distribution == 3:
            height = (sizing[0] - 150) / 1.05
            width = sizing[1] / 1.4
        elif distribution == 4:
            height = (sizing[0] - 150) / 1.05
            width = sizing[1] / 1.6
        elif distribution == 5:
            height = (sizing[0] - 150) / 1.05
            width = sizing[1] / 1.8
        elif distribution == 6:
            height = (sizing[0] - 150) / 1.05
            width = sizing[1] / 2.1
        elif distribution == 7:
            height = (sizing[0] - 150) / 1.05
            width = sizing[1] / 2.55
        elif distribution == 8:
            height = (sizing[0] - 180) / 1.05
            width = sizing[1] / 3.3
        elif distribution == 9:
            height = (sizing[0] - 180) / 1.05
            width = sizing[1] / 4.5

        # set style of div accordingly
        div_style_dic["height"] = str(height + 1) + "px"
        div_style_dic["width"] = str(width + 1) + "px"

        return height, width, height, width, div_style_dic

    @app.callback(
        Output("ngl_molecule_viewer", "downloadImage"),
        Output("ngl_molecule_viewer", "imageParameters"),
        Input("download_molecule_button", "n_clicks"),
        Input("filename_input", "value"),
        Input("mol_name_storage", "data"),
    )
    def download_molecule(button_clicks: int, filename_input: str, mol_names: str):
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        if filename_input is None or filename_input == "":
            filename_input = mol_names

        image_parameters = {
            # Antialiasing, makes image smoother
            "antialias": True,
            # change the background from black to transparent
            "transparent": True,
            # trim background to edges of molecule, only works with transparent
            "trim": True,
            "defaultFilename": filename_input,
        }

        download_image = False

        if ctx.triggered_id == "download_molecule_button":
            download_image = True

        return download_image, image_parameters

    @app.callback(
        Output("left_col", "width"),
        Output("right_col", "width"),
        Input("distribution_slider", "value"),
    )
    def set_space_distribution(left_width):
        right_width = 12 - left_width

        return left_width, right_width


def get_callbacks(
    app,
    df: DataFrame,
    original_id_col: list,
    umap_paras: dict,
    output_d: Path,
):
    @app.callback(
        Output("graph", "figure"),
        Input("dd_menu", "value"),
        Input("dim_red_radio", "value"),
    )
    def update_graph(selected_value: str, dim_red: "str"):
        """
        Renders new graph for selected drop down menu value
        :param selected_value: selected column of dropdown menu
        :return: graph to be displayed
        """
        # Check whether an input is triggered
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # In case dropdown menu is being cleared
        if selected_value is None:
            raise PreventUpdate

        # Set up umap flag
        umap_flag = True if dim_red == "UMAP" else False

        fig = Visualizator.render(
            df,
            selected_column=selected_value,
            original_id_col=original_id_col,
            umap_flag=umap_flag,
        )

        # Set up title of graph
        title = ""
        if dim_red == "PCA":
            title = dim_red
        elif dim_red == "UMAP":
            title = (
                dim_red
                + f"<br>n_neighbours: {umap_paras['n_neighbours']},"
                + f" min_dist: {umap_paras['min_dist']}, metric: {umap_paras['metric']}"
            )
        fig.update_layout(title={"text": title, "y": 0.98, "x": 0.4})

        return fig

    @app.callback(
        Output("disclaimer_modal", "is_open"),
        Input("disclaimer_modal_button", "n_clicks"),
    )
    def close_disclaimer_modal(button):
        if button:
            return False

        return True

    @app.callback(
        Output("help_modal", "is_open"),
        Input("help_button", "n_clicks"),
    )
    def open_help_modal(button):
        if button:
            return True

        return False

    @app.callback(
        Output("graph_offcanvas", "is_open"), Input("graph_settings_button", "n_clicks")
    )
    def handle_graph_canvas(button_click):
        if button_click:
            return True

    @app.callback(
        Output("html_download_toast", "is_open"),
        Input("html_dd", "value"),
        Input("html_download_button", "n_clicks"),
        Input("dim_red_radio", "value"),
    )
    def create_html(dd_value: str, button: int, dim_red: str):
        # Check whether an input is triggered
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        if ctx.triggered_id == "html_download_button":
            # Set up umap flag
            umap_flag = True if dim_red == "UMAP" else False

            fig = Visualizator.render(df, dd_value, original_id_col, umap_flag)
            fig.write_html(output_d / f"3Dspace_{dd_value}_{dim_red}.html")

            return True
