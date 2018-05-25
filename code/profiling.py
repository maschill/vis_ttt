import cProfile
from elasticsearch import Elasticsearch, helpers
import elasticSearch
import json
import pandas as pd

def getfieldnames(f, data):
	#data = json.load(f)
	return(data['columns'])

INDEX_NAME='dlrmetadata'
TYPE='doc'

#elasticSearch.updateFile(data, meta, fn, es)
es = Elasticsearch([{'host':'localhost','port': 9200}])

datafile = '/home/lea/Dokumente/FSU/vis_ttt/data/data/m_airrsinf.tsv'
metafile = '/home/lea/Dokumente/FSU/vis_ttt/data/meta/m_airrsinf.json'

data = open(datafile, 'r')
meta = open(metafile, 'r')
meta.seek(0)
data.seek(0)
fn = 'm_airrsinf'
es.indices.create(index=INDEX_NAME, ignore=400)

print('##############################################')
metadata = json.loads(meta.read())  # .decode('utf-8').replace('\0', ''))
fieldnames = getfieldnames(meta, metadata)
# constants = getConstants(meta, metadata)
df = pd.read_csv(data, names=fieldnames, sep='\t')
# df = timeConv(df)
# df = markMissesAndOutliers(df)
# reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
# helpers.bulk(es, reader, index=INDEX_NAME, doc_type=TYPE)
# print('Adding documents to ' + INDEX_NAME + '/' + TYPE)
'''
data_dict = []
for idx, row in df.iterrows():
	data_dict.append({
		'_op_type': 'index',
		'_'
		row.to_dict()}
	)
#	# data_dict.update(constants)
es.bulk(body=data_dict, index=INDEX_NAME, doc_type=TYPE)
'''
print('start bulk upload')
#https://stackoverflow.com/questions/43981275/index-json-files-in-elasticsearch-using-python
bulk_action = [
	{
		'_op_type': 'index',
		'_index': 'dlrmetadata',
		'_id': row[0],
		'_type': 'doc',
		'_source': row.to_dict()
	}
	for idx, row in df.iterrows()
	]
#print(bulk_action)
res = helpers.parallel_bulk(es, bulk_action)
print(res)
#for chunk in pyelasticsearch.bulk_chunks(documents(), docs_per_chunk=500, bytes_per_chunk=10000):
#	es.bulk(chunk, doc_type=TYPE, index=INDEX_NAME)

#print(len(data_dict))
#datafile = open(args.data)
#metafile = open(args.meta)
#addDocument(data=datafile, meta=metafile, INDEX_NAME=args.INDEX_NAME, TYPE=TYPE)
#elasticSearch.updateFile(data, meta, fn, es)
#cProfile.run('elasticSearch.updateFile(data, meta, fn, es)')
