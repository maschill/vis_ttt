'''
script to load tsv files with column description in json file
'''

from elasticsearch import helpers, Elasticsearch
import csv, json
import glob, os
import argparse
import datetime
from outlierEvenMore import timeConv, delMissesAndOutliers, markMissesAndOutliers
import pandas as pd

def getfieldnames(f, data):
	#data = json.load(f)
	return [w.replace('.','') for w in  data['columns']]

def getConstants(f, data):
	fieldnames = []
	values = []
	for const in data['constants']:
		fieldnames += [const['id']]
		values += [const['value']]
	const = dict(zip(fieldnames, values))
	return const

def get_location(row):
	# es input format: 
	# {
	# 	"type": <type>,
	# 	"coordinates": <list of coordinates depending on type>
	# }

	## tsv file format
	## POLYGON(([list of coordinates])) or
	## 8 seperate fields giving corners
	## POINT((coordinates)) or
	location = []

	for _,item in row.iteritems():
		if type(item)==str and item.startswith("POLYGON(("):
			#POLYGON((lon lat, lon2 lat2, ...., lonN latN))
			location = [[float(x) for x in pair.strip().split(" ")] for pair in item[9:-2].split(",")]
			return {"type":"polygon", "coordinates":[location]}
			#return {"type": "polygon", "coordinates": [[[1.0,1.0],[1.0,10.0],[10.0,10.0],[10.0,1.0],[1.0,1.0]]]}
		elif type(item)==str and item.startswith("POINT("):
			location = [float(x) for x in item[6:-1].split(" ")]  
			return {"type": "point", "coordinates":[location]}
		return {"type": "polygon", "coordinates": [[[1.0,1.0],[1.0,10.0],[10.0,10.0],[10.0,1.0],[1.0,1.0]]]}

def addDocument(data, meta, filename, INDEX_NAME, TYPE, es):
	print('##############################################')
	meta.seek(0)
	print('metadata load')
	metadata = json.loads(meta.read().decode('utf-8').replace('\0', ''))
	print('get fieldnames')
	fieldnames = getfieldnames(meta, metadata)
	print('get constants')
	constants = getConstants(meta, metadata)
	print('read data')
	df = pd.read_csv(data, names=fieldnames, sep='\t', low_memory=False)
	#df = timeConv(df)
	#df = markMissesAndOutliers(df)
	df['filename'] = filename

		# reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
		#helpers.bulk(es, reader, index=INDEX_NAME, doc_type=TYPE)
		# print('Adding documents to ' + INDEX_NAME + '/' + TYPE)
	#for idx, row in df.iterrows():
	#	data_dict = row.to_dict()
		#data_dict.update(constants)
	#	es.index(index=INDEX_NAME, doc_type=TYPE, body=data_dict)
	if "mission0" in constants:
		df["mission0"] = constants["mission0"]
	print('DF PREPARED')
	bulk_action = [
		{
			'_op_type': 'index',
			'_index': INDEX_NAME,
			'_id': row[0],
			'_type': TYPE,
			'_source': row.to_json()
				#'location': get_location(row)
		}
		for idx, row in df.iterrows()
	]

	# Bulk upload files and check if successful
	success, failed = 0, 0
	for success, info in helpers.parallel_bulk(es, bulk_action, chunk_size=10):
		if not success:
			failed += 1
		else:
			success += 1
	print(data, 'added to elasticsearch index ', INDEX_NAME, '\n',
	      'success: ', success, 'failed: ', failed)

def updateFile(datafile, metafile, filename, es):
	print('START UPLOAD : ', filename)

	datafile.seek(0)
	metafile.seek(0)
	metadata = json.loads(metafile.read().decode('utf-8').replace('\0', ''))

	# Index wird angelegt, falls er noch nicht existiert
	if not es.indices.exists('dlrmetadata'):
		dlrmetadatabody = {
				"settings": {
					"number_of_shards": 1,
					"number_of_replicas": 0,
				},
				"mappings":{
					"doc":{
						"properties":{
						}
					}
				}
		}
		column_types_dict = {
			"GeoObject": {
				"type": "geo_shape",
				"tree": "quadtree",
				"precision": "1000m",
				"distance_error_pct": 0.001,
				"ignore_malformed": True
			},
			"Date": {
				"type": "date",
				"format": "yyyy-MM-dd HH:mm:ss.SSS",
			},
			"Double": {
				"type": "double",
			},
			"Integer": {
				"type": "integer",
			},
			"Character": {
				"type": "text",
			},
			"Identifier": {
				"type": "keyword",
			},
			"Boolean": {
				"type": "boolean",
			},
			"Text": {
				"type": "text",
			}
		}

		coldesc = json.load(open('/home/lea/Dokumente/FSU/vis_ttt/data/meta/_columnDescription.json'))
		for col in coldesc:
			if 'id' in col:
				column_type = col['type']
				dlrmetadatabody['mappings']['doc']['properties'][str(col['id'])] = column_types_dict[column_type]

		print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', '\n', dlrmetadatabody, '\n', 'XXXXXXXXXXXXXXXXXXXXXXXXXXX')
		es.indices.create(index='dlrmetadata', body=dlrmetadatabody)

	# Falls Daten schon existieren und nur upgedated werden sollen, werden sie gelöscht
	if es.indices.exists('dlrmetadata'):
		es.delete_by_query(index='dlrmetadata', doc_type='doc', body={'query': {'match': {'filename': filename}}})
	print('add document...')
	addDocument(datafile, metafile, filename, INDEX_NAME='dlrmetadata', TYPE='doc', es=es)

	print('check indices')
	if es.indices.exists('dataoverview'):
		es.delete_by_query(index='dataoverview', doc_type='doc', body={'query': {'match': {'filename': filename}}})
	now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

	constants = getConstants(metafile, metadata)
	filenames = {'filename': filename.split('.')[0],
	             'size': len(datafile.read()),
	             'addDate': now,
	             'updateDate': now}
	filenames.update(constants)
	print('add ', filenames, 'to dataoverview')
	es.index(index='dataoverview', doc_type='doc', body=filenames)
	print('DONE WITH ', filename)

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='Create index and load tsv file in elaseicsearch.')
	parser.add_argument('--data', help='tsv file to parse')
	parser.add_argument('--meta', help='Metadata for tsv file')
	parser.add_argument('--folder', help='folder containing all files (.tsv) to upload. Metadata and data should be in '
	                                     'same folder vis_ttt/data/meta and vis_ttt/data/data')
	parser.add_argument('--INDEX_NAME', default='dlrmetadata',
	                    help='elasticsearch index name to which document will be added')
	args = parser.parse_args()

	TYPE = 'doc'

	#meta='../data/meta/m_airrsgtc.json' #data='../data/data/m_airrsgtc.tsv'

	es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
	print('Initialize elasticsearch with', es)

	# create an index, ignore if already exists (done automatically by es.index)
	# es.indices.create(index=INDEX_NAME, ignore=400)

	# Now add documents
	if args.folder:
		# e.g. '/home/lea/Dokumente/FSU/vis_ttt/data/data/*'
		files = glob.glob(os.path.join(args.folder, '*'))

		for data in files:
			meta = data.split('/')
			#TYPE = meta[-1].split('.')[0]
			meta[-2] = 'meta'
			meta[-1] = meta[-1].replace('.tsv', '.json')
			meta = '/'.join(meta)
			datafile = open(data)
			metafile = open(meta)
			addDocument(data=datafile, meta=metafile, INDEX_NAME= args.INDEX_NAME, TYPE=TYPE, es=es)
			now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
			filenames = {'filename': data.split('/')[-1].split('.')[0],
			             'size': os.path.getsize(data),
			             'addDate': now,
			             'updateDate': now}
			es.index(index='dataoverview', doc_type='doc', body=filenames)
	else:
		#TYPE = args.meta.split('/')[-1].split('.')[0]
		datafile = open(args.data)
		metafile = open(args.meta)
		addDocument(data=datafile, meta=metafile, INDEX_NAME=args.INDEX_NAME, TYPE=TYPE, es=es)
		now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
		filenames = {'filename': args.data.split('/')[-1].split('.')[0],
		             'size': os.path.getsize(args.data),
		             'addDate': now,
		             'updateDate': now}
		es.index(index='dataoverview', doc_type='doc', body=filenames)