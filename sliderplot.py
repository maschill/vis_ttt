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
all_data = AjaxDataSource(data_url='http://localhost:8000/api/_bokeh_data', method="POST", polling_interval=2000, if_modified=True, mode="replace")
# all_data.data = {'starttime1':[], 'westboundingcoor0':[], 'eastboundingcoor0':[], 'northboundingcoo0':[], 'southboundingcoo0':[], 'percentageofpote1':[] }


# print('data: ',all_data.data)
'''q =  {
        "bool": {
            "must": [{
                "exists": {
                    "field" : 'percentageofpote1'
                }
            },
            {
                "exists": {
                    "field": 'westboundingcoor0',
                }
            },
            {
                "exists": {
                    "field": 'eastboundingcoor0'
                }
            },
            {
                "exists": {
                    "field": 'northboundingcoo0'
                }
            },
            {
                "exists": {
                    "field": 'southboundingcoo0'
                }
            }
            ]
        }
    }


all_data = []
resp = es.search(index='dlrmetadata', doc_type='doc', body={"query":q}, size=10000,   scroll = '2m')
sid = resp['_scroll_id']
scroll_size = resp['hits']['total']
while (scroll_size > 0):
    all_data = all_data + [d['_source'] for d in resp['hits']['hits']]
    resp = es.scroll(scroll_id = sid, scroll = '2m')
    # Update the scroll ID
    sid = resp['_scroll_id']
    # Get the number of results that we returned in the last scroll
    scroll_size = len(resp['hits']['hits'])
'''
# df = all_data.to_df()

# print(df)
# df['starttime1']=pd.to_datetime(df['starttime1'])
# print('something something ... dark side')

# print('Dataframe received')
# # Change values to datetime for plotting issues
# #data['starttime1'] = pd.to_datetime(data['starttime1'])
# data = df.copy()
# data['month_year'] = data.starttime1.dt.to_period('M')
# data['year'] = data.starttime1.dt.year
# data['month'] = data.starttime1.dt.month
# data['scene_lat'] = (data['westboundingcoor0'] + data['eastboundingcoor0']) / 2
# data['scene_lon'] = (data['northboundingcoo0'] + data['southboundingcoo0']) / 2

gj = json.load(open('ne_110m_coastline.geojson'))   


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
# source = ColumnDataSource(data=dict(x=data['scene_lat'] , y=data['scene_lon'], c=data['percentageofpote1'] ))



plot.circle(x='scene_lat', y='scene_lon', color='percentageofpote1', source=all_data, line_width=3, alpha=0.6)


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
    view = all_data.loc[all_data['year'] == a]
    print(len(view))
    x = view['scene_lat']
    y = view['scene_lon']
    #c = view['percentageofpote1']
    print(min(view['percentageofpote1']), max(view['percentageofpote1']))
    colors = ["#%02x%02x%02x" % (int(255/(r+1)), 100, 100) for r in all_data['percentageofpote1']]
    all_data.data = dict(x=x, y=y, c=colors)

for w in [date]:
    w.on_change('value', update_data)


# Set up layouts and add to document
inputs = widgetbox(text, date)

curdoc().add_root(row(inputs, plot, ))
curdoc().title = "Sliders"
curdoc().plot_height=400
curdoc().plot_width=800
