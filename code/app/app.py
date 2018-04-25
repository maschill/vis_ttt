from flask import Flask, render_template, request
from elasticsearch import Elasticsearch

es = Elasticsearch([{'host':'localhost','port': 9200}])
app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def index():

	q = request.args.get('q')
	#q = request.form.get('q')

	if q is not None:
		resp = es.search(index='dlrmetadata', doc_type='doc', body={"query": {"prefix": {"name": q}}})
		return render_template("index.html", q=q, request=resp)

	return render_template('index.html')

# routine for part 1
# returns list of all types which are our datasets
def showdatasets():
	datasets = [index for index in es.indices.get('*')]
	return datasets

if __name__ == '__main__':
	app.run(debug=True, port=8000)