## Setup
1. Install Elasticsearch >=6.x
2. Install Python 3 ([Anaconda](https://conda.io/docs/user-guide/install/windows.html) or venv)
3. Make sure all requirements as in requirements_python.txt are met (pip install -r requirements_python.txt or conda install --yes --file requirements_python.txt)

## Config file
4. Set names for elasticsearch index in config file vis_ttt/elasticsearch/elconfig.json. Where indexes are used as follows:
"DATA": for actual data (.tsv files)
"COLUMNDESCRIPTION": for _columnDescription.json located in vis_ttt/elasticsearch/
"DATAOVERVIEW": metadata about .tsv files (e.g. size, last update, upload information) used on website in 'Data Overview'
"UPDATE_COLUMNDESCRIPTION": values: "True" or "FALSE" if true, column description will be updated if new file is uploaded / old file is updated.

## Run application
5. change directory to vis_ttt/code/app
6. run python app.py
7. enjoy. 
