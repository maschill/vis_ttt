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

import os, glob, json
import pandas as pd
import numpy as np

#functions
def read_data(filename):
    data = pd.read_csv(filename, sep='\t')
    meta = json.load(open('data/' + filename.split('/')[-1].replace('.tsv', '.json')))
 
def get_location(row):
    location = []

    for _,item in row.iteritems():
        if type(item)==str and item.startswith("POLYGON(("):
            #POLYGON((lon lat, lon2 lat2, ...., lonN latN))
            location = [[float(x) for x in pair.strip().split(" ")] for pair in item[9:-2].split(",")]
            return {"type":"polygon", "coordinates":[location]}
        #return {"type": "polygon", "coordinates": [[[1.0,1.0],[1.0,10.0],[10.0,10.0],[10.0,1.0],[1.0,1.0]]]}
        elif type(item)==str and item.startswith("POINT("):
            location = [float(x) for x in item[6:-1].split(" ")]  
    return {"type": "point", "coordinates":[location]}
    return {"type": "point", "coordinates": [0.0,0.0]}

# Set up data
N = 200
x = np.linspace(0, 4*np.pi, N)
y = np.sin(x)
source = ColumnDataSource(data=dict(x=x, y=y))
datafiles = sorted(glob.glob('data/*.tsv'))
metafiles = sorted(glob.glob('data/*.json'))
filename = datafiles[57]
try:
    meta = json.load(open('data/' + filename.split('\\')[-1].replace('.tsv', '.json')))
except FileNotFoundError:
    meta = json.load(open('data/' + filename.split('/')[-1].replace('.tsv', '.json')))

data = pd.read_csv(filename, names=meta['columns'], sep='\t')

# These are the parameters I wanted to take a look at
water_parameters = ['percentageofpote1', 'westboundingcoor0', 
                    'eastboundingcoor0', 'northboundingcoo0', 'southboundingcoo0']

# Change values to datetime for plotting issues
data['starttime1'] = pd.to_datetime(data['starttime1'])
data['month_year'] = data.starttime1.dt.to_period('M')
months_str = [str(float(str(x).replace('-', '.'))) for x in data.month_year]
data['month_year_str'] = months_str
months = [float(str(x).replace('-', '.')) for x in data.month_year]
data['month_year_fl'] = months
data['year'] = data.starttime1.dt.year
data['month'] = data.starttime1.dt.month
data['scene_lat'] = (data['westboundingcoor0'] + data['eastboundingcoor0']) / 2
data['scene_lon'] = (data['northboundingcoo0'] + data['southboundingcoo0']) / 2

# Set up data
source = ColumnDataSource(data=dict(x=data['scene_lat'] , y=data['scene_lon'] ))


# Set up plot
plot = figure( title="my sine wave", height=500, width=1000,
              tools="crosshair,pan,reset,save,wheel_zoom",
              x_range=[data['scene_lat'].min(), data['scene_lat'].max()], 
              y_range=[data['scene_lon'].min(), data['scene_lon'].max()])

plot.circle('x', 'y', source=source, line_width=3, line_alpha=0.6)


# Set up widgets
text = TextInput(title="title", value='my sine wave')
date = Slider(title="date", value=2010, start=2000, end=2018, step=1)

# Set up callbacks
def update_title(attrname, old, new):
    plot.title.text = text.value

text.on_change('value', update_title)

def update_data(attrname, old, new):

    # Get the current slider values
    a = date.value

    # Generate the new curve
    view = data.loc[data['year'] == a]
    print(len(view))
    x = view['scene_lat']
    y = view['scene_lon']

    source.data = dict(x=x, y=y)

for w in [date]:
    w.on_change('value', update_data)


# Set up layouts and add to document
inputs = widgetbox(text, date)

curdoc().add_root(row(inputs, plot, ))
curdoc().title = "Sliders"
curdoc().plot_height=500
curdoc().plot_width=1000
