from flask import Flask, render_template, request, jsonify
from elasticsearch import Elasticsearch
from files import filesfromEL
import tempfile
import sys, json
import pandas as pd

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.embed import server_document

col1 = [''.join(['val', str(x)]) for x in range(10)]
col2 = [x for x in range(10)]
col3 = ['red', 'green', 'blue', 'green', 'red', 'blue', 'red', 'yellow', 'red', 'green']
df = pd.DataFrame({"col1":col1, "col2":col2, "col3":col3})

es = Elasticsearch([{'host':'localhost','port': 9200}], timeout=1000)
app = Flask(__name__)

from api import bp as api_bp
app.register_blueprint(api_bp, url_prefix='/api')

sys.path.insert(0,'../')
import  elasticSearch

Files = filesfromEL(es=es)
#print(Files)

def make_plot():
	plot = figure(plot_height=300, sizing_mode='scale_width')

	x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
	y = [2**v for v in x]

	plot.line(x, y, line_width=4)

	script, div = components(plot)
	return script, div

def get_measured_variables():
	q = {"_source": ["type", "id"], "query": {"terms": {"type": ["double"]}}}
	resp = es.search(index='columndescription', doc_type='doc', body=q, size=1000)
	filename_field = [x['_source']['id'] for x in resp['hits']['hits']]

	variable_description = []
	for col in filename_field:
		q = {"size": 0,
		     "aggregations": {
			     "variance_field": {
				     "extended_stats": {
					     "field": col
				     }
			     }
		     }
		     }
		resp = es.search(index='dlrmetadata', doc_type='doc', body=q, size=100,
		                 filter_path=['aggregations.variance_field'])
		if not 'lon' in col and not 'lat' in col and not 'coo' in col:# and col != 'heightofambiguit0' and col != 'tilt_angle0' and col != 'meandifferenceto1':
			resp['aggregations']['variance_field']['fname'] = col
			if resp['aggregations']['variance_field']['count'] > 0:
				variable_description += [resp['aggregations']['variance_field']]

	return variable_description

@app.route('/')
def index():
	script = server_document("http://localhost:5006/sliderplot")
	
	d3data = get_measured_variables()
	docnum = es.count(index='dlrmetadata', filter_path=['count'])['count']
	levels  = df.col3.unique()
	min_c2 = df.col2.min()
	max_c2 =  df.col2.max()
	return render_template('home.html', levels=levels, min_c2=min_c2, max_c2=max_c2, script=script, d3data=d3data, docnum=docnum)

@app.route('/data_servant', methods=['POST', 'GET'])
def data_servant():
	# if request.method=='POST':
	# 	f1 = request.args.get('f1')
	# 	f1 = request.args.get('f2')
	# 	f1 = request.args.get('f3')
	json_req = request.get_json()
	level = json_req["colors"]
	min_col2 = json_req["slider_min"]
	print(level)
	df_res = df[(df.col3 == level) & (df.col2 >= int(min_col2))]
	return jsonify(status='sucess' , content='this is the new Content', **df_res.to_dict() )


#this is called when clicking the upload button
@app.route('/_upload_button', methods=['GET', 'POST'])
def _upload_button():
	if request.method=='POST':
		#arg = request.args.get('student_id', 0)
		print('Someone clicked on Upload')
		data_files = request.files.getlist('file')
		meta_files = request.files.getlist('file2')

		for meta, data in zip(meta_files, data_files):
			fn = meta.filename.split('.')[0]
			meta.seek(0)
			data.seek(0)
			elasticSearch.updateFile(data, meta, fn, es)
		return jsonify(status="success")
	return jsonify(status='something went wrong')

#this is called when clicking the delete all button
@app.route('/_delete_button', methods=['GET', 'POST'])
def _delete_button():
	#delete index....
	if es.indices.exists(['dataoverview']):
		es.indices.delete(index=['dataoverview'], ignore=[400, 404])
	
	if es.indices.exists(['dlrmetadata']):
		es.indices.delete(index=['dlrmetadata'], ignore=[400, 404])
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
	if Files is not None:
		if q is not None:
			resp = es.search(index='dataoverview', doc_type='doc', body={"query": {"match": {"filename": q}}})
			if resp['hits']['total'] == 0:
				msg='file does not exist'
			else:
				msg='file exists'
			return render_template("data.html", q=q, response=resp, message=msg,files=Files)
		else:
			return render_template('data.html', files=Files)
	else:
		return render_template('data.html', files=Files)

# routine for part 1
# returns list of all types which are our datasets
#def showdatasets():
#	datasets = [index for index in es.indices.get('*')]
#	return datasets

if __name__ == '__main__':
	app.run(debug=True, port=8000)
