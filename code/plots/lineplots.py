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

import requests
import os, glob, json
import pandas as pd
import numpy as np

###

from elasticsearch import Elasticsearch
import datetime
import pandas as pd

es = Elasticsearch('http://localhost:9200')

# input =

cloud_parameters = ['cloud_score_aver2', 'manual_cloud_sco0', 'manual_cloud_sco3',
                    'manual_cloud_sco6', 'manual_cloud_sco9']


# Load data
datafiles = sorted(glob.glob('data/data/*'))
metafiles = sorted(glob.glob('data/meta/*'))
filename = datafiles[10]
meta = json.load(open('data/meta/' + filename.split('/')[-1].replace('.tsv', '.json')))
data = pd.read_csv(filename, names=meta['columns'], sep='\t')
print('Dataframe received')

# These are the parameters I wanted to take a look at
#cloud_Score_Average,manual_Cloud_Score_LL, manual_Cloud_Score_LR, manual_Cloud_Score_UL, manual_Cloud_Score_UR
cloud_parameters = ['cloud_score_aver2', 'manual_cloud_sco0', 'manual_cloud_sco3',
                    'manual_cloud_sco6', 'manual_cloud_sco9']
# Change values to datetime for plotting issues
data['starttime1'] = pd.to_datetime(data['starttime1'])

#
data['year'] = data.starttime1.dt.year
data['month'] = data.starttime1.dt.month

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
plot = figure(
	width=800,
	height=400,
	title='World Countries',
	x_axis_label='Longitude',
	y_axis_label='Latitude',
)
# colors = cbrewer['Paired'][12]
for (index, country) in enumerate(worldmapdata):
	plot.patch(
		x=worldmapdata[country]['x'],
		y=worldmapdata[country]['y'],
		# color=colors[index%len(colors)],
		alpha=.6
	)

# Set up data
source = ColumnDataSource(data=dict(x=data['scene_lat'], y=data['scene_lon'], c=data['percentageofpote1']))

plot.circle('x', 'y', color='c', source=source, line_width=3, alpha=0.6)

# Set up widgets
text = TextInput(title="title", value='Percantage of pote1')
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
	# c = view['percentageofpote1']
	print(min(view['percentageofpote1']), max(view['percentageofpote1']))
	colors = ["#%02x%02x%02x" % (int(255 / (r + 1)), 100, 100) for r in data['percentageofpote1']]
	source.data = dict(x=x, y=y, c=colors)


for w in [date]:
	w.on_change('value', update_data)

# Set up layouts and add to document
inputs = widgetbox(text, date)

curdoc().add_root(row(inputs, plot, ))
curdoc().title = "Sliders"
curdoc().plot_height = 500
curdoc().plot_width = 1000
