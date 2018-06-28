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



@bp.route('/st/<starttime>', methods=['GET'])
def get_starttime(starttime):
	resp = es.search(index='dlrmetadata', doc_type='doc', body={"query": {"match": {"starttime1":
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

		query = {
			"must": [
				{"range": {"starttime1": rang["starttime1"]}},
				{
					"exists": {
						"field": 'polygonmeanlon',
					}
				},
				{
					"exists": {
						"field": 'polygonmeanlat'
					}
				}

			],
		}

		# Add geo shape filter if values entered
		geo_filter = {
			"geo_shape": {
				"location": {
					"shape": {
						"type": "point"
					},
					"relation": "INTERSECTS"
				}
			}
		}

		if request.args.get('measure_variable') != '':
			query['must'] += [{'exists': {'field': request.args.get('measure_variable')}}]

		if request.args.get('latitude_longitude') != "" and request.args.get('latitude_longitude') != 'None':
			geo_filter['geo_shape']['location']['shape']['coordinated'] = [float(request.args.get('latitude_longitude').split(',')[0].strip().replace('_', '.')),
											float(request.args.get('latitude_longitude').split(',')[1].strip().replace('_', '.'))]
			query['filter'] = geo_filter

		#if "mission0" in request.args:
	#		match['mission0'] = request.args.get("mission0")

		if "starttimeMin" in request.args:
			rang["starttime1"]["gte"] = request.args.get("starttimeMin")
		if "starttimeMax" in request.args:
			rang["starttime1"]["lte"] = request.args.get("starttimeMax")
			
		rang['stoptime1']['format'] = "yyyy-MM-dd"
		rang['starttime1']['format'] = "yyyy-MM-dd"

		if match['mission0'] != '':
			query["must"].append({"match": {"mission0":request.args.get("mission0")}}) 

		q = {"bool":query}
		print('QUERY', q)

		resp = es.search(index='dlrmetadata', doc_type='doc', body={"query":q}, size=100)

		data = [d['_source'] for d in resp['hits']['hits']]
		data = pd.DataFrame(data)
		data['starttime1']=pd.to_datetime(data['starttime1'])
		
		data['month_year'] = data.starttime1.dt.to_period('M')
		data['month'] = data.starttime1.dt.month
		data['scene_lat'] = data['polygonmeanlat']
		data['scene_lon'] = data['polygonmeanlon']
		data['val'] = data[request.args.get("measure_variable")]
		data["rlat"] = data['scene_lat'].apply(lambda x: round(x))
		data["rlon"] = data['scene_lon'].apply(lambda x: round(x))
		# print(data.groupby(['year', 'rlat', 'rlon'])['val'].mean())
		data = data[data["val"] != 0]
		data.dropna(axis=0)
		data['year'] = pd.to_numeric(data.starttime1.dt.year)
		mm = {}
		data.to_json("data.json")
		data.index = data.index.map(str)
		tdict = data[['scene_lat', 'scene_lon', 'year', "val", "mission0"]].to_dict(orient='index')

		mm["miny"] = int(data['year'].min())
		mm["maxy"] = int(data['year'].max())
		# with open('data.json', 'w') as file:
		# 	json.dump(data, file)
		#print('QUERY RESPONSE: ', resp)
		return jsonify(data=tdict, minmax=mm)
	except Exception as e:
		print(e)
		return jsonify({ "error": "500 - internal server error" })

@bp.route('/all', methods=['GET'])
def get_all():
	pass