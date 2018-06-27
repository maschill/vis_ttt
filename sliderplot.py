''' Present an interactive function explorer with slider widgets.
Scrub the sliders to change the properties of the ``sin`` curve, or
type into the title text box to update the title of the plot.
Use the ``bokeh serve`` command to run the example by executing:
    bokeh serve sliders.py
at your command prompt. Then navigate to the URL
    http://localhost:5006/sliders
in your browser.
'''
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Slider, TextInput
from bokeh.plotting import figure
from bokeh.models.sources import RemoteSource, AjaxDataSource
import requests
import os, glob, json
import pandas as pd
import numpy as np

###

from elasticsearch import Elasticsearch
import datetime
import pandas as pd

#es = Elasticsearch('http://localhost:9200')
print('GET DATA')
<<<<<<< HEAD
all_data = AjaxDataSource(data_url='http://localhost:8000/api/_bokeh_data', method="POST",
                          polling_interval=2000, if_modified=True, mode="replace")

# Set up worldmap data
# from: https://gist.github.com/tonyfast/994f37c4540ce91c6784
countries = requests.get('https://rawgit.com/johan/world.geo.json/master/countries.geo.json').json()

countryObject = {}
for country in countries['features']:
    countryObject[country['properties']['name']] = {
        'x': [x[0] for x in country['geometry']['coordinates'][0]],
        'y': [x[1] for x in country['geometry']['coordinates'][0]],
    }
worldmapdata = pd.DataFrame(countryObject)
=======

all_data = pd.read_json("code/app/data.json")

gj = json.load(open('ne_110m_coastline.geojson'))   


>>>>>>> e7f846dee1dfa6a2cadf387c048e368d3183ad49
plot = figure(
    width = 800, 
    height=400, 
    title='World Countries', 
    x_axis_label='Longitude',
    y_axis_label='Latitude',
)



for i in  gj['features']:
    plot.line([x[0] for x in i['geometry']['coordinates']], [x[1] for x in i['geometry']['coordinates']])

# These are the parameters I wanted to take a look at
# water_parameters = ['percentageofpote1', 'westboundingcoor0',
#                     'eastboundingcoor0', 'northboundingcoo0', 'southboundingcoo0']

# Set up data
<<<<<<< HEAD
# source = ColumnDataSource(data=dict(x=data['scene_lat'] , y=data['scene_lon'], c=data['percentageofpote1'] ))
#var = all_data.data['measure_variable']
plot.circle(x='scene_lat', y='scene_lon', color='measure_variable', source=all_data, line_width=3, alpha=0.6)
=======
source = ColumnDataSource(data=dict(x=all_data['scene_lat'] , y=all_data['scene_lon'], c=all_data['percentageofpote1'] ))



plot.circle(x='x', y='y', color='c', source=source, line_width=3, alpha=0.6)
>>>>>>> e7f846dee1dfa6a2cadf387c048e368d3183ad49


# Set up widgets
text = TextInput(title="title", value='measure_variable')
date = Slider(title="date", value=2010, start=2000, end=2018, step=1)

# Set up callbacks
def update_title(attrname, old, new):
    plot.title.text = text.value

text.on_change('value', update_title)

def update_data(attrname, old, new):

    # Get the current slider values
    #a = date.value

    # Generate the new curve
    #view = all_data.loc[all_data['year'] == a]
    #print(len(view))
    x = view['scene_lat']
    y = view['scene_lon']
<<<<<<< HEAD
    #colors = ["#%02x%02x%02x" % (int(255/(r+1)), 100, 100) for r in all_data.data['percentageofpote1']]
    all_data.data = dict(x=x, y=y)#, c=colors)
=======
    #c = view['percentageofpote1']
    # print(min(view['percentageofpote1']), max(view['percentageofpote1']))
    colors = ["#%02x%02x%02x" % (int(255/(r+1)), 100, 100) for r in all_data['percentageofpote1']]
    source.data = dict(x=x, y=y, c=colors)
>>>>>>> e7f846dee1dfa6a2cadf387c048e368d3183ad49

for w in [date]:
    w.on_change('value', update_data)


# Set up layouts and add to document
inputs = widgetbox(text, date)

curdoc().add_root(row(inputs, plot, ))
curdoc().title = "Sliders"
curdoc().plot_height=400
curdoc().plot_width=800
