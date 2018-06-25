from api import bp
from elasticsearch import Elasticsearch
from flask import jsonify, request
from flask.json import JSONDecoder
import datetime, json
from collections import defaultdict
import pandas as pd

from bokeh.client import pull_session
from bokeh.embed import server_session

es = Elasticsearch('http://localhost:9200')

@bp.route('/st/<starttime>', methods=['GET'])
def get_starttime(starttime):
	resp = es.search(index='dlrmetadata', doc_type='doc', body={"query": {"match": {"starttime1":
		            datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M:%S.%f')}}})
	return jsonify(resp)

@bp.route("/_bokeh_data", methods=["GET", "POST"])
def bokeh_serv():
	with open('data.json', 'r') as infile:
		data = json.load(infile)
		all_data = [d['_source'] for d in data['hits']['hits'][:20]]
		all_data = pd.DataFrame(all_data)
		for bla in all_data:
			print('row: ', bla)
	return JSONDecoder(all_data)


@bp.route('/filter', methods=['GET', 'POST'])
def filter_data():
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

	resp = es.search(index='dlrmetadata', doc_type='doc', body={"query":q}, size=500)

	with open('data.json', 'w') as file:
		json.dump(resp, file)
	#print('QUERY RESPONSE: ', resp)
	return jsonify(resp)

@bp.route('/all', methods=['GET'])
def get_all():
	pass