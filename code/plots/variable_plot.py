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
all_data = AjaxDataSource(data_url='http://localhost:8000/api/_bokeh_data', method="POST",
                          polling_interval=2000, if_modified=True, mode="replace")

#parameters_of_interest = ['resolution2', 'percentageofpote1', 'cloud_score_aver2']
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
    x_range=(all_data.data['x_range_min'],all_data.data['x_range_max']),
    y_range=(all_data.data['y_range_min'],all_data.data['y_range_max'])
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

#global:
param_choice = data['resolution2']
#

#source = ColumnDataSource(data=dict(x=data['scene_lat'] , y=data['scene_lon'], c=param_choice ))
plot.circle('scene_lat', 'scene_lon', source=all_data, line_width=3, alpha=0.6)

# Set up widgets
text = TextInput(title="title", value='Daily Resolution')
print("You've made it this far, traveller!")

year_slider = Slider(title="Year", value=all_data['year'].min(), start=all_data['year'].min(), end=all_data['year'].max(), step=1)
month_slider = Slider(title="Month", value=all_data['year'].min(), start=all_data['year'].min(), end=all_data['year'].max(), step=1)
day_slider = DateSlider(title="Day", start=all_data['date'].min(), end=all_data['date'].max(), value=all_data['date'].min(), step=1)

#year_slider = Slider(title="Year", value=data['year'].min(), start=data['year'].min(), end=data['year'].max(), step=1)
#month_slider = Slider(title="Month", value=data['year'].min(), start=data['year'].min(), end=data['year'].max(), step=1)
#day_slider = DateSlider(title="Day", start=data['date'].min(), end=data['date'].max(), value=data['date'].min(), step=1)


#date = DateSlider(title="Day", start=data['date'].min(), end=data['date'].max(), value=data['date'].min(), step=1)
#param_button_group = RadioButtonGroup(labels=["Resolution", "Potential Water", "Cloud Coverage", "Gelbstoff"], active=0)
time_button_group = RadioButtonGroup(labels=["Yearly", "Monthly", "Daily"], active=0)
# Set up callbacks

#global:
chosen_slider = month_slider
chosen_timeline = data['month_year_fl']
inputs = widgetbox(chosen_slider, time_button_group) #(text, )
#

def update_title(attrname, old, new):
    plot.title.text = text.value

text.on_change('value', update_title)

def update_data(attrname, old, new):
    global chosen_slider
    # Get the current slider values
    # Generate the new curve
    view = data.loc[chosen_timeline == chosen_slider.value] ##MUST CHANGE THIS FOR CHANGING DATE SLIDERS
    x = view['scene_lat']
    y = view['scene_lon']
    #c = view['percentageofpote1']
    colors = ["#%02x%02x%02x" % (int(255/(r+1)), 100, 100) for r in param_choice]
    source.data = dict(x=x, y=y, c=colors)

for w in [chosen_slider]:
    w.on_change('value', update_data)
'''
def param_radio_handler(new):
    global chosen_slider
    global chosen_timeline
    view = data.loc[chosen_timeline == chosen_slider.value]
    print 'Parameter button option ' + str(new) + ' selected.'
    global param_choice
    if str(new) == "0":
        param_choice = data['resolution2']
    if str(new) == "1":
        param_choice = data['percentageofpote1']
    if str(new) == "2":
        param_choice = data['cloud_score_aver2']
    if str(new) == "3":
        param_choice = data['gelbstoffmax0']
    colors = ["#%02x%02x%02x" % (int(255/(r+1)), 100, 100) for r in param_choice]
    x = view['scene_lat']
    y = view['scene_lon']
    source.data = dict(x=x, y=y, c=colors)
param_button_group.on_click(param_radio_handler)
'''
#OK
def time_radio_handler(new):
    global param_choice
    global inputs
    global chosen_slider
    global chosen_timeline
    view = data.loc[chosen_timeline == chosen_slider.value]
    print 'Time button option ' + str(new) + ' selected.'
    if str(new) == "0":
        chosen_slider = year_slider
    if str(new) == "1":
        chosen_slider = month_slider
    if str(new) == "2":
        chosen_slider = day_slider
    colors = ["#%02x%02x%02x" % (int(255/(r+1)), 100, 100) for r in param_choice]
    x = view['scene_lat']
    y = view['scene_lon']
    source.data = dict(x=x, y=y, c=colors)
    inputs = widgetbox(chosen_slider, param_button_group, time_button_group) #(text,
time_button_group.on_click(time_radio_handler)
#OK


# Set up layouts and add to document

curdoc().add_root(column(inputs, plot,  ))
curdoc().title = "Best UX ever"
curdoc().plot_height=600
curdoc().plot_width=920
