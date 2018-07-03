from flask import Flask, render_template, request, jsonify, make_response  
from elasticsearch import Elasticsearch
from files import filesfromEL
import tempfile
import sys, json
import pandas as pd

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.embed import server_document



from flask_cors import CORS

df = pd.read_json("data_default.json")
df.to_json('data.json')
es = Elasticsearch([{'host':'localhost','port': 9200}], timeout=1000)
app = Flask(__name__)

from api import bp as api_bp
app.register_blueprint(api_bp, url_prefix='/api')

cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


sys.path.insert(0,'../')
import  elasticSearch

#Files = filesfromEL(es=es)
# Get config files
indexnames = json.load(open('../../elasticsearch/elconfig.json'))


def make_plot():
	plot = figure(plot_height=300, sizing_mode='scale_width')

	x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
	y = [2**v for v in x]

	plot.line(x, y, line_width=4)

	script, div = components(plot)
	return script, div

def get_measured_variables():
	variable_description = []
	if es.indices.exists(indexnames['COLUMNDESCRIPTION']) and es.indices.exists(indexnames['DATA']):
		q = {"_source": ["type", "id", "label"], "query": {"terms": {"type": ["double"]}}}
		resp = es.search(index=indexnames['COLUMNDESCRIPTION'], doc_type='doc', body=q, size=1000)
		filename_field = [[x['_source']['id'], x['_source']['label']] for x in resp['hits']['hits']]

		for col in filename_field:
			q = {"size": 0,
			     "aggregations": {
				     "variance_field": {
					     "extended_stats": {
						     "field": col[0]
					    }
				    }
			    }
			}
			resp = es.search(index=indexnames['DATA'], doc_type='doc', body=q, size=100,
			                 filter_path=['aggregations.variance_field'])
			if not 'lon' in col[0] and not 'lat' in col[0] and not 'coo' in col[0]:# and col != 'heightofambiguit0' and col != 'tilt_angle0' and col != 'meandifferenceto1':
				resp['aggregations']['variance_field']['measure_var'] = col[0]
				resp['aggregations']['variance_field']['fname'] = col[1]
				if resp['aggregations']['variance_field']['count'] > 0:
					variable_description += [resp['aggregations']['variance_field']]

	return variable_description

@app.route('/csv/')
def download_csv():
	##get current data
	csv = pd.read_json("data.json").to_csv()
	response = make_response(csv)
	cd = 'attachment; filename=data.csv'
	response.headers['Content-Disposition'] = cd 
	response.mimetype='text/csv'

	return response

@app.route('/')
def index():
	d3data = get_measured_variables()
	docnum = 1
	if es.indices.exists(indexnames['DATA']):
		docnum = es.count(index=indexnames['DATA'], filter_path=['count'])['count']
	return render_template('home.html',  d3data=d3data, docnum=docnum)

@app.route('/data_servant', methods=['POST', 'GET'])
def data_servant():
	json_req = request.get_json()
	level = json_req["colors"]
	min_col2 = json_req["slider_min"]
	print(level)
	df_res = df[(df.col3 == level) & (df.col2 >= int(min_col2))]
	return jsonify(status='sucess' , content='this is the new Content', **df_res.to_dict() )

@app.route("/bokeh", methods=['POST', 'GET'])
def bokeh_plots():
	script = server_document("http://localhost:5006/sliderplot")
	return render_template("bokeh.html", script=script)

#this is called when clicking the upload button
@app.route('/_upload_button', methods=['GET', 'POST'])
def _upload_button():
	if request.method =='POST':
		#arg = request.args.get('student_id', 0)
		print('Someone clicked on Upload')
		data_files = request.files.getlist('file')
		meta_files = request.files.getlist('file2')

		for meta, data in zip(meta_files, data_files):
			mfn = meta.filename.split('.')
			dfn = data.filename.split('.')
			if mfn[0] == dfn[0] and mfn[1] == 'json' and dfn[1] == 'tsv':
				meta.seek(0)
				data.seek(0)
				elasticSearch.updateFile(data, meta, mfn[0], es)
			else:
				print('DATA (.tsv) and META (.json) file do not match \n',
				      'Stopped uploading: ', meta.filename,' and ', data.filename)

		return jsonify(status="success")
	return jsonify(status='something went wrong')

#this is called when clicking the delete all button
@app.route('/_delete_button', methods=['GET', 'POST'])
def _delete_button():
	#read config file again
	indexnames = json.load(open('../../elasticsearch/elconfig.json'))

	#delete index....
	if es.indices.exists([indexnames['DATAOVERVIEW']]):
		es.indices.delete(index=[indexnames['DATAOVERVIEW']], ignore=[400, 404])
	
	if es.indices.exists([indexnames['DATA']]):
		es.indices.delete(index=[indexnames['DATA']], ignore=[400, 404])

	if es.indices.exists([indexnames['COLUMNDESCRIPTION']]):
		es.indices.delete(index=[indexnames['COLUMNDESCRIPTION']], ignore=[400, 404])
	#then rebuild - just update by upload
	Files = filesfromEL(es=es)
	print('All indexes deleted')
	return render_template('data.html', files=Files)
	#return jsonify(status="success")


@app.route('/data', methods=['GET','POST'])
def data():
	Files = filesfromEL(es=es)
	q = request.args.get('q')
	#q = request.form.get('q')
	if es.indices.exists(indexnames['DATAOVERVIEW']):
		if Files is not None:
			if q is not None:
				resp = es.search(index=indexnames['DATAOVERVIEW'], doc_type='doc', body={"query": {"match": {"filename": q}}})
				if resp['hits']['total'] == 0:
					msg='file does not exist'
				else:
					msg='file exists'
				return render_template("data.html", q=q, response=resp, message=msg,files=Files)
			else:
				return render_template('data.html', files=Files)
		else:
			return render_template('data.html', files=Files)
	else:
		 return render_template("data.html", files={})

# routine for part 1
# returns list of all types which are our datasets
#def showdatasets():
#	datasets = [index for index in es.indices.get('*')]
#	return datasets

if __name__ == '__main__':
	app.run(debug=True, port=8000)
