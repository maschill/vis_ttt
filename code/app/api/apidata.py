from api import bp
from elasticsearch import Elasticsearch
from flask import jsonify, request
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
		return jsonify(json.load(infile))


@bp.route('/filter', methods=['GET', 'POST'])
def filter_data():
	rang = defaultdict(dict)
	match = defaultdict(dict)

	with pull_session(url="http://localhost:5006/sliderplot") as session:
	    # update or customize that session
		print(session.document.roots[0].children[1].title.text)
		session.document.roots[0].children[1].title.text = "Special Sliders For A Specific User!"


	print(match)
	match['mission0'] = ''

	query = {
		"must":[
			{"range":{"stoptime1":rang["stoptime1"]}},
			{"range":{"starttime1": rang["starttime1"]}}
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


	if request.args.get('longitude') != "" and request.args.get('latitude') != "":
		geo_filter['geo_shape']['location']['shape']['coordinated'] = [float(request.args.get('longitude').replace('_', '.')),
						                float(request.args.get('latitude').replace('_', '.'))]
		query['filter'] = geo_filter


	#if "mission0" in request.args:
#		match['mission0'] = request.args.get("mission0")

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

	if match['mission0'] != '':
		query["must"].append({"match": {"mission0":request.args.get("mission0")}}) 

	q = {"bool":query}


	print('mission: ', request.args.get("mission0"))
	print('q: ', query)
	print(request.args.get("starttimeMin"))

	resp = es.search(index='dlrmetadata', doc_type='doc', body={"query":q}, size=500)


	with open("data.json", "w") as file:
		json.dump(resp,file)

	return jsonify(resp)

@bp.route('/all', methods=['GET'])
def get_all():
	pass