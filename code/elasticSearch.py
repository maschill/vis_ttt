'''
script to bulkload tsv files with column description in json file
'''

from elasticsearch import helpers, Elasticsearch
import csv, json
import argparse

#parser = argparse.ArgumentParser(description='Create index and load tsv file in elaseicsearch.')
#parser.add_argument('file', help='tsv file to parse')
#parser.add_argument('meta', help='Metadata for tsv file')
#args = parser.parse_args()

# Now add data
meta = 'data/meta/m_airrsgtc.json'
data = 'data/data/m_airrsgtc.tsv'

INDEX_NAME = 'dlrmetadata' #collection of documents that have similar characteristics
TYPE = 'm_airrsgtc'

es = Elasticsearch([{'host':'localhost','port': 9200}])
print(es)
# create an index, ignore if already exists
es.indices.create(index=INDEX_NAME, ignore=400)

def getfieldnames(file):
	with open(file) as f:
		data = json.load(f)
		return(tuple(data['columns']))

with open(data) as f:
	fieldnames = getfieldnames(meta)
	reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
	#helpers.bulk(es, reader, index=INDEX_NAME, doc_type=TYPE)
	i = 0
	for row in reader:
		es.index(index=INDEX_NAME, doc_type=TYPE, id=i, body=row)
		i += 1

#res=es.get(index=INDEX_NAME,doc_type=TYPE, id='dims_op_pl_eoweb1_XXXXB00000000295446012384')
#print(res)
