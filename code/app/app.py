from flask import Flask, render_template, request
from elasticsearch import Elasticsearch
from files import files

es = Elasticsearch([{'host':'localhost','port': 9200}])
app = Flask(__name__)

@app.route('/')
def index():
	return render_template('home.html')

#@app.route('/data')
#def data():
#	return render_template('data.html', files = Files)

@app.route('/data', methods=['GET','POST'])
def data():
	Files = files()

	q = request.args.get('q')
	#q = request.form.get('q')

	if q is not None:
		resp = es.search(index='dataoverview', doc_type='doc', body={"query": {"match": {"filename": q}}})
		return render_template("data.html", q=q, response=resp, files=Files)
	else:
		return render_template('data.html', files=Files)

# routine for part 1
# returns list of all types which are our datasets
#def showdatasets():
#	datasets = [index for index in es.indices.get('*')]
#	return datasets

if __name__ == '__main__':
	app.run(debug=True, port=8000)
