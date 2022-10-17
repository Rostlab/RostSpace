# ProtSpace3D

This is a bachelor thesis project, 
Development of protein-embedding visualization tool.

## Installing dependencies

Python-poetry(https://python-poetry.org/) is used for installing the dependencies. Follow the instruction 
on the website to install poetry.
After that run

```shell
poetry install
```

to install the dependencies for this project.

## Running the script

The script to be executed is processing.py with the arguments:

    ->  -d          Name of the folder which holds the required data, .h5 .csv & .fasta (String)
    ->  -b          Name of the files which are in the data folder, requires equal names (String)
    ->  --sep       The character which seperates the columns in the .csv file (Character)
    ->  --uid_col   The column number which holds the unique ID, starting from 0 (Integer)
    ->  --html_cols If set, html file(s) of the selected column(s) is saved in data directory, starting from 1 ignoring the uid_col (Integer)

Example:

```shell
poetry run python app.py -d data/ex1 -b VA
```
