''' Present an interactive function explorer with slider widgets.
Scrub the sliders to change the properties of the ``sin`` curve, or
type into the title text box to update the title of the plot.
Use the ``bokeh serve`` command to run the example by executing:
    bokeh serve sliders.py
at your command prompt. Then navigate to the URL
    http://localhost:5006/sliders
in your browser.
'''



from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Slider, DateSlider, Button, RadioButtonGroup, TextInput
from bokeh.plotting import figure

import requests
import os, glob, json
import pandas as pd
import numpy as np
import datetime
from datetime import date

###

# Load data
datafiles = sorted(glob.glob('../../data/data/*'))
metafiles = sorted(glob.glob('../../data/meta/*'))
filename = datafiles[57]
print(filename)
meta = json.load(open('../../data/meta/' + filename.split('\\')[-1].replace('.tsv', '.json')))
data = pd.read_csv(filename, names=meta['columns'], sep='\t')
print('Dataframe received')

#Declare all variables here
starttime = 'starttime1'
#parameters_of_interest = ['resolution2', 'percentageofpote1', 'cloud_score_aver2']

#Load polygons, define center point
def get_polygons(row):
    for _,item in row[1].iteritems():
        if type(item)==str and item.startswith("POLYGON(("):
            return item

def getpolygonmean(polygon):
    p = polygon.strip(')POLYGON(').split(',')
    coords = np.array([[float(x) for x in ort.strip().split(' ')] for ort in p])
    meanlon, meanlat = coords.mean(axis=0)
    return(meanlon, meanlat)


# Change values to datetime for plotting issues
data['polygon_center'] = [getpolygonmean(get_polygons(row)) for row in data.iterrows()]
data['starttime1'] = pd.to_datetime(data[starttime])
data['month_year'] = data.starttime1.dt.to_period('M')
data['year'] = data.starttime1.dt.year
data['month'] = data.starttime1.dt.month
data['scene_lat'] = [x[0] for x in data['polygon_center']]
data['scene_lon'] = [x[1] for x in data['polygon_center']]
months_str = [str(float(str(x).replace('-', '.'))) for x in data.month_year]
data['month_year_str'] = months_str
months = [float(str(x).replace('-', '.')) for x in data.month_year]
data['month_year_fl'] = months
data['day'] = data.starttime1.dt.day
days = [str(x).replace(str(x),str(x)) for x in data.day]
data['day'] = days
data['dmy_str'] = data['month_year_str'] + "." + data['day']
data['dmy_val'] = [float(str(x).replace('.', '')) for x in data.dmy_str]
data['date'] = data['dmy_str']
data['date'] = [date(int(data['year'][i]), int(data['month'][i]), int(data['day'][i])) for i,j in enumerate(data['dmy_str'])]


#==================
# Set up worldmap data
#==================

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
    height=500,
    title='World Countries',
    x_axis_label='Longitude',
    y_axis_label='Latitude',
    x_range=(data['scene_lat'].min(),data['scene_lat'].max()),
    y_range=(data['scene_lon'].min(),data['scene_lon'].max())
)
#colors = cbrewer['Paired'][12]
for (index,country) in enumerate(worldmapdata):
    plot.patch(
        x=worldmapdata[country]['x'],
        y=worldmapdata[country]['y'],
        #color=colors[index%len(colors)],
        alpha = .6
    )
#==================
#end world map creation
#==================


#==================
#create plot
#==================


# Set up data
param_choice = data['resolution2']
source = ColumnDataSource(data=dict(x=data['scene_lat'] , y=data['scene_lon'], c=param_choice ))
plot.circle('x', 'y', color='c', source=source, line_width=3, alpha=0.6)

# Set up widgets
text = TextInput(title="title", value='Daily Resolution')
print("You've made it this far, traveller!")

date_slider = Slider(title="Year", value=data['year'].min(), start=data['year'].min(), end=data['year'].max(), step=1)
#date = DateSlider(title="Month", start=data['year'].min(), end=data['year'].max(), value=data['year'].min(), step=1)
#date = DateSlider(title="Day", start=data['date'].min(), end=data['date'].max(), value=data['date'].min(), step=1)
param_button_group = RadioButtonGroup(labels=["Resolution", "Potential Water", "Cloud Coverage"], active=0)
time_button_group = RadioButtonGroup(labels=["Yearly", "Monthly", "Daily"], active=0)
# Set up callbacks

#Define global
a = date_slider.value

def update_title(attrname, old, new):
    plot.title.text = text.value

text.on_change('value', update_title)

def update_data(attrname, old, new):
    # Get the current slider values
    global a
    a = date_slider.value
    # Generate the new curve
    view = data.loc[data['year'] == a] ##MUST CHANGE THIS FOR CHANGING DATE SLIDERS
    x = view['scene_lat']
    y = view['scene_lon']
    #c = view['percentageofpote1']
    colors = ["#%02x%02x%02x" % (int(255/(r+1)), 100, 100) for r in param_choice]
    source.data = dict(x=x, y=y, c=colors)

for w in [date_slider]:
    w.on_change('value', update_data)

def param_radio_handler(new):
    global a
    view = data.loc[data['year'] == a]
    print 'Parameter button option ' + str(new) + ' selected.'
    global param_choice
    if str(new) == "0":
        param_choice = data['resolution2']
    if str(new) == "1":
        param_choice = data['percentageofpote1']
    if str(new) == "2":
        param_choice = data['cloud_score_aver2']
    colors = ["#%02x%02x%02x" % (int(255/(r+1)), 100, 100) for r in param_choice]
    x = view['scene_lat']
    y = view['scene_lon']
    source.data = dict(x=x, y=y, c=colors)

param_button_group.on_click(param_radio_handler)


# Set up layouts and add to document
inputs = widgetbox(text, date_slider, param_button_group, time_button_group)

curdoc().add_root(column(inputs, plot,  ))
curdoc().title = "Best UX ever"
curdoc().plot_height=500
curdoc().plot_width=800
