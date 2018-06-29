import datetime
import glob
import os
import collections
import json

def files():
	now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
	files = glob.glob(os.path.join('../../data/data/', '*'))
	print(files)
	filenames = {}
	for data in files:
		f = data.split('/')[-1]
		filenames[f] = now

	orderedfilenames = collections.OrderedDict(sorted(filenames.items()))
	print(orderedfilenames)
	return orderedfilenames

def filesfromEL(es):
	indexnames = json.load(open('../../elasticsearch/elconfig.json'))

	if es.indices.exists(indexnames['DATAOVERVIEW']):
		res = es.search(index=indexnames['DATAOVERVIEW'], size=200,
		                body={"query": {"match_all": {}}, "_source": ["filename","size","updateDate", "success", "failed", "failedids"]})
		filenames = [x['_source']['filename'] for x in res['hits']['hits']]
		size = [x['_source']['size'] for x in res['hits']['hits']]
		update = [x['_source']['updateDate'] for x in res['hits']['hits']]
		success = [x['_source']['success'] for x in res['hits']['hits']]
		failed = [x['_source']['failed'] for x in res['hits']['hits']]
		failedids = [x['_source']['failedids'] for x in res['hits']['hits']]
		tabledata = sorted(zip(filenames, zip(size, update, success, failed, failedids)), key = lambda x: x[1][0], reverse=True)
		orderedfilenames = collections.OrderedDict(tabledata)
	else:
		orderedfilenames = None
	return orderedfilenames

if __name__== '__main__':
	Files = files()
	print(Files)