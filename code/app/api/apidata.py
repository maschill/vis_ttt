from api import bp
from elasticsearch import Elasticsearch
from flask import jsonify, request
from flask.json import JSONDecoder
import datetime, json
from collections import defaultdict
import pandas as pd

from flask_cors import CORS
from flask_cors import cross_origin
from datetime import date

from bokeh.client import pull_session
from bokeh.embed import server_session

es = Elasticsearch('http://localhost:9200')

# Get config files
indexnames = json.load(open('../../elasticsearch/elconfig.json'))


@bp.route('/st/<starttime>', methods=['GET'])
def get_starttime(starttime):
	resp = es.search(index=indexnames['DATA'], doc_type='doc', body={"query": {"match": {"starttime1":
		            datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M:%S.%f')}}})
	return jsonify(resp)


# Change values to datetime for plotting issues
'''
data['polygon_center'] = [getpolygonmean(get_polygons(row)) for row in data.iterrows()]
data['starttime1'] = pd.to_datetime(data[starttime])
data['month_year'] = data.starttime1.dt.to_period('M')
data['year'] = data.starttime1.dt.year
data['month'] = data.starttime1.dt.month
months_str = [str(float(str(x).replace('-', '.'))) for x in data.month_year]
data['month_year_str'] = months_str
months = [float(str(x).replace('-', '.')) for x in data.month_year]
data['month_year_fl'] = months
data['day'] = data.starttime1.dt.day
days = [str(x).replace(str(x),str(x)) for x in data.day]
data['day'] = days
data['dmy_str'] = data['month_year_str'] + "." + data['day']
data['dmy_val'] = [float(str(x).replace('.', '')) for x in data.dmy_str]
# data['month_date'] = data['month'], data['year']
data['date'] = [date(int(data['year'][i]), int(data['month'][i]), int(data['day'][i])) for i,j in enumerate(data['dmy_str'])]
'''

@bp.route("/_bokeh_data", methods=["GET", "POST", "OPTIONS"])
@cross_origin(allow_headers=['Content-Type'])
def bokeh_serv():
	with open('data.json', 'r') as infile:
		data = json.load(infile)
		all_data = [d['_source'] for d in data['hits']['hits']]
		all_data = pd.DataFrame(all_data)
		df = all_data
		df['starttime1']=pd.to_datetime(df['starttime1'])
		data = df

		data['month_year'] = data.starttime1.dt.to_period('M')
		data['year'] = data.starttime1.dt.year
		data['month'] = data.starttime1.dt.month
		data['scene_lat'] = data['polygonmeanlat']
		data['scene_lon'] = data['polygonmeanlon']
		months_str = [str(float(str(x).replace('-', '.'))) for x in data.month_year]
		data['month_year_str'] = months_str
		months = [float(str(x).replace('-', '.')) for x in data.month_year]
		data['month_year_fl'] = months
		data['day'] = data.starttime1.dt.day
		days = [str(x).replace(str(x), str(x)) for x in data.day]
		data['day'] = days
		data['dmy_str'] = data['month_year_str'] + "." + data['day']
		data['dmy_val'] = [float(str(x).replace('.', '')) for x in data.dmy_str]
		# data['month_date'] = data['month'], data['year']
		data['date'] = [date(int(data['year'][i]), int(data['month'][i]), int(data['day'][i])) for i, j in
		                enumerate(data['dmy_str'])]

		datadict = data[['scene_lat', 'scene_lon',
		              'year', 'month', 'day', 'date']].to_dict(orient="list")
		datadict['measure_variable'] = data['{}'.format(request.args.get('measure_variable'))]

		#ranges for plot
		datadict['x_range_min'] = data['scene_lat'].min()
		datadict['x_range_max'] = data['scene_lat'].max()
		datadict['y_range_min'] = data['scene_lon'].min()
		datadict['y_range_max'] = data['scene_lon'].max()

		print(datadict['measure_variable'])
		return jsonify(datadict)

@bp.route('/filter', methods=['GET', 'POST'])
def filter_data():
	try:
		rang = defaultdict(dict)
		match = defaultdict(dict)

		match['mission0'] = ''
		
		if "starttimeMin" in request.args:
			rang["starttime1"]["gte"] = request.args.get("starttimeMin")
		if "starttimeMax" in request.args:
			rang["starttime1"]["lte"] = request.args.get("starttimeMax")
			
		rang['starttime1']['format'] = "yyyy-MM-dd"

		q = { 
			"query": {
				"bool": {
					"must": [
								{"range": {"starttime1": rang["starttime1"]}},
								{
									"exists": {
										"field": 'polygonmeanlon',
									}
								},                        
								{
									"exists": {
										"field": 'starttime1',
									}
								}, 
								{
									"exists": {
										"field": 'polygonmeanlat'
									}
								}
							],
					},
			},
				"size": 0,
				"aggs": {      
					"lat_hist":{
						"histogram": {
							"field": "polygonmeanlat",
								"interval": 2,
								"min_doc_count": 1
						},

						"aggs": {
							"lon_hist":{
								"histogram":{
									"field": "polygonmeanlon",
									"interval": 2,
									"min_doc_count": 1
								},
							
						
							"aggs": {
								"avg_somethingsomething":{
									"date_histogram": {
										"field": "starttime1",
										"interval": "month",
										"format" : "yyyy-MM",
										"min_doc_count": 1
										},

									"aggs": {
										"avg_val":{
											"avg": {
												"field": request.args.get("measure_variable")
											},
										},
										"cnt":{
											"terms": {
												"field": request.args.get("measure_variable")
											}
										}   
									},
								}
							}
						},
					},
				},
			}
		}

		geo_filter = None
		
		if request.args.get('latitude_longitude') != "" and request.args.get('latitude_longitude') != 'None':
			lat,lon = [float(request.args.get('latitude_longitude').split(',')[0].strip().replace('_', '.')),
											float(request.args.get('latitude_longitude').split(',')[1].strip().replace('_', '.'))]


		# Add geo shape filter if values entered
			geo_filter =  [
						{
					"range":{
						"polygonmeanlat":{
						"gte": lat-20,
						"lte": lat+20,}
					}
					
				},
				{
					"range":{
						"polygonmeanlon":{
						"gte": lon-20,
						"lte": lon+20,}
					}
					
				}
				]

		if request.args.get('measure_variable') != '':
			q['query']['bool']['must'] += [{'exists': {'field': request.args.get('measure_variable')}}]


			q['query']["bool"]['filter'] = geo_filter


		if match['mission0'] != '':
			q['query']['bool']["must"].append({"match": {"mission0":request.args.get("mission0")}}) 

		print('QUERY', q)
		resp = es.search(index=indexnames['DATA'], doc_type='doc', body=q, size=1)

		values = []
		for lat_buck in resp["aggregations"]["lat_hist"]['buckets']:
			for lon_buck in lat_buck["lon_hist"]["buckets"]:
				for avg_buck in lon_buck["avg_somethingsomething"]["buckets"]:
					values.append([lat_buck['key'], lon_buck['key'], avg_buck['key_as_string'], avg_buck["avg_val"]["value"]])
					
		data = pd.DataFrame(values, index=None, columns = ['scene_lat', 'scene_lon', 'year', 'val'])
		data = data[data.val > 0]
		mm = {}
		data.index = data.index.map(str)
		tdict = data[['scene_lat', 'scene_lon', 'year', "val"]].to_dict(orient='index')
		data['year_'] = [(pd.to_numeric(x.replace('-', '.'))) for x in data['year']]
		#data['year_'] = [(pd.to_numeric(x[:4])) for x in data['year']]
		yearmonthmin = data['year_'].min()
		mm["miny"] = int(data['year_'].min())
		mm["maxy"] = int(data['year_'].max())
		mm["minmonth"] = '{}'.format(yearmonthmin)[-2:]

		return jsonify(data=tdict, minmax=mm)
	except Exception as e:
		print(e)
		return jsonify({ "error": "500 - internal server error" })

@bp.route('/all', methods=['GET'])
def get_all():
	pass