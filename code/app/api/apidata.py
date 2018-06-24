from api import bp
from elasticsearch import Elasticsearch
from flask import jsonify, request
import datetime
from collections import defaultdict

es = Elasticsearch('http://localhost:9200')

@bp.route('/<starttime>', methods=['GET'])
def get_starttime(starttime):
	resp = es.search(index='dlrmetadata', doc_type='doc', body={"query": {"match": {"starttime1":
		            datetime.datetime.strptime(starttime, '%Y-%m-%d %H:%M:%S.%f')}}})
	return jsonify(resp)

@bp.route('/filter', methods=['GET', 'POST'])
def filter_data():
	rang = defaultdict(dict)
	match = defaultdict(dict)
	match['mission0'] = ''

	if "mission0" in request.args:
		match['mission0'] = request.args.get("mission0")

	if "starttimeMin" in request.args:
		rang["starttime1"]["gte"] = request.args.get("starttimeMin")
	if "stoptimeMin" in request.args: 
		rang["stoptime1"]["gte"] = request.args.get("stoptimeMin")
	if "starttimeMax" in request.args:
		rang["starttime1"]["lte"] = request.args.get("starttimeMax")
	if "stoptimeMax" in request.args:
		rang["stoptime1"]["lte"] = request.args.get("stoptimeMax")
		
	rang['stoptime1']['format'] = "yyyy-MM-dd"
	rang['starttime1']['format'] = "yyyy-MM-dd"

	query = {
		"must":[
			{"range":{"stoptime1":rang["stoptime1"]}},
			{"range":{"starttime1": rang["starttime1"]}}
		],
		#Geo shape
		"filter": {
			"geo_shape": {
				"location": {
					"shape": {
						"type": "point",
						"coordinates": [float(request.args.get('longitude').replace('_', '.')),
						                float(request.args.get('latitude').replace('_', '.'))
						                ]
						#"coordinates": [15.0,15.0]
						#"type": "polygon",
						#"coordinates": [[[1.0, 1.0], [3.0, 3.0], [10.0,10.0], [15.0,15.0], [1.0,1.0]]]
					},
					"relation": "INTERSECTS"
				}
			}
		}
	}

	if match['mission0'] != '':
		query["must"].append({"match": {"mission0":request.args.get("mission0")}}) 

	q = {"bool":query}


	print('mission: ', request.args.get("mission0"))
	print('q: ', query)
	print(request.args.get("starttimeMin"))

	resp = es.search(index='dlrmetadata', doc_type='doc', body={"query":q}, size=500)
	print(resp)
	return jsonify(resp)

@bp.route('/all', methods=['GET'])
def get_all():
	pass