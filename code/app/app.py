from flask import Flask, render_template, request, jsonify
from elasticsearch import Elasticsearch
from files import filesfromEL
from ... import elasticSearch

es = Elasticsearch([{'host':'localhost','port': 9200}])
app = Flask(__name__)

Files = filesfromEL(es=es)
print(Files)

@app.route('/')
def index():
	return render_template('home.html')

#this is called when clicking the upload button
@app.route('/_upload_button', methods=['GET', 'POST'])
def _upload_button():
	if request.method=='POST':
		#arg = request.args.get('student_id', 0)
		print('Someone clicked on Upload')
		fileList = request.files.getlist('file')
		fileList2 = request.files.getlist('file2')
		for fi in fileList:
			elasticSearch.addFile()
			print(fi.filename)
			print(type(fi))
		for fi2 in fileList2:
			print(fi2.filename, fi2.content_length)
		return jsonify(status="success")
	return jsonify(error='something went wrong')

#this is called when clicking the delete all button
@app.route('/_delete_button', methods=['GET', 'POST'])
def _delete_button():
	#delete index....
	#es.indices.delete(index='dataoverview', ignore=[400, 404])
	#then rebuild

	print('Someone clicked on DELETE ALL')
	return jsonify(status="success")


@app.route('/data', methods=['GET','POST'])
def data():
	q = request.args.get('q')
	#q = request.form.get('q')

	if q is not None:
		resp = es.search(index='dataoverview', doc_type='doc', body={"query": {"match": {"filename": q}}})
		if resp['hits']['total'] == 0:
			msg='file does not exist'
		else:
			msg='file exists'
		return render_template("data.html", q=q, response=resp, message=msg,files=Files)
	else:
		return render_template('data.html', files=Files)

# routine for part 1
# returns list of all types which are our datasets
#def showdatasets():
#	datasets = [index for index in es.indices.get('*')]
#	return datasets

if __name__ == '__main__':
	app.run(debug=True, port=8000)
