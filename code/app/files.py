import datetime
import glob
import os
import collections

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
	if es.indices.exists('dataoverview'):
		res = es.search(index='dataoverview', body={"query": {"match_all": {}}, "_source": ["filename","size","updateDate"]})
		filenames = [x['_source']['filename'] for x in res['hits']['hits']]
		size = [x['_source']['size'] for x in res['hits']['hits']]
		update = [x['_source']['updateDate'] for x in res['hits']['hits']]
		orderedfilenames = collections.OrderedDict(sorted(zip(filenames, zip(size, update))))
	else:
		orderedfilenames = None
	return orderedfilenames

if __name__== '__main__':
	Files = files()
	print(Files)