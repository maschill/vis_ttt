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
import numpy as np

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

def clean_row(row):
	r = []
	for idx,item in row.iteritems():
		if type(item)==str and item.startswith("POLYGON(("):
			row[idx].replace('N(', 'N (')

			#POLYGON((lon lat, lon2 lat2, ...., lonN latN))
			#location = [[float(x) for x in pair.strip().split(" ")] for pair in item[9:-2].split(",")]
			#return {"type":"polygon", "coordinates":[location]}
			#return {"type": "polygon", "coordinates": [[[1.0,1.0],[1.0,10.0],[10.0,10.0],[10.0,1.0],[1.0,1.0]]]}
		elif type(item)==str and item.startswith("POINT("):
			row[idx].replace('T(', 'T (')
			#location = [float(x) for x in item[6:-1].split(" ")]
			#return {"type": "point", "coordinates":[location]}
		#return {"type": "polygon", "coordinates": [[[1.0,1.0],[1.0,10.0],[10.0,10.0],[10.0,1.0],[1.0,1.0]]]}
		return row


def bulk_action(df, INDEX_NAME, TYPE):
	for idx, row in df.iterrows():
		#row = clean_row(row)
		#print(idx, ': ' , row)
		yield {
			'_op_type': 'index',
			'_index': INDEX_NAME,
			'_id': row[0],
			'_type': TYPE,
			'_source': row.to_json()
				#'location': get_location(row)
		}

def addDocument(data, meta, filename, INDEX_NAME, TYPE, es):
	print('##############################################')
	meta.seek(0)
	print('metadata load')
	metadata = json.loads(meta.read().decode('utf-8').replace('\0', ''))
	print('get fieldnames')
	meta.seek(0)
	fieldnames = getfieldnames(meta, metadata)
	print('get constants')
	meta.seek(0)
	constants = getConstants(meta, metadata)
	print('read data')
	df = pd.read_csv(data, names=fieldnames, sep='\t', low_memory=False)
	df = timeConv(df)
	df = markMissesAndOutliers(df)
	df['filename'] = filename
	if "mission0" in constants:
		df["mission0"] = constants["mission0"]
	print('DF PREPARED')

	for idx in df.columns:
		#column isglobal0 not only Bool type as stated in description
		if idx == 'isglobal0':
			# and filename in ['m_irsp6awifsp', 'm_irsp6lissiiip', 'm_irsp6lissivpmono']:
			df.drop(columns='isglobal0', inplace=True)
		elif type(df[idx][0]) == str and df[idx][0].startswith("POLYGON(("):
		#	df[idx] = df[idx].apply(lambda x: x.replace("POLYGON((", "POLYGON (("))
			df[idx] = df[idx].apply(lambda x: x.replace("POLYGON ((0 0, 0 0, 0 0, 0 0, 0 0))", "POINT (0 0)") if type(x) == str else x)
		#elif type(df[idx][0]) == str and df[idx][0].startswith("POINT("):
		#	df[idx] = df[idx].apply(lambda x: x.replace("POINT(", "POINT ("))

	print(df.dtypes)
	# Bulk upload files and check if successful
	success, failed = 0, 0
	for success, info in helpers.parallel_bulk(es, bulk_action(df, INDEX_NAME, TYPE), chunk_size=50, raise_on_error=True):
		if not success:
			failed += 1
		else:
			success += 1
	print(data, 'added to elasticsearch index ', INDEX_NAME, '\n',
	      'success: ', success, 'failed: ', failed)

def updateFile(datafile, metafile, filename, es):
	print('START UPLOAD : ', filename)

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
				#"type": "text"
				"type": "geo_shape",
				#"tree": "geohash",#"quadtree",
				"precision": "100km",
				# for 2mB file, disk space required by precision:
				#100 km : 5 mb
				# 10 km : 27 mb
				#  1 km : too much (1117 docs.count: 375mb)
				#"distance_error_pct": 0.025,
				"ignore_malformed": True
			},
			"Date": {
				"type": "date",
				"format": "yyyy-MM-dd HH:mm:ss.SSS",
				"ignore_malformed": True
			},
			"Double": {
				"type": "double"
			},
			"Integer": {
				"type": "integer"
			},
			"Character": {
				"type": "text"
			},
			"Identifier": {
				"type": "keyword"
			},
			"Boolean": {
				"type": "boolean"
			},
			"Text": {
				"type": "text"
			}
		}

		coldesc = json.load(open('../../data/meta/_columnDescription.json'))
		for col in coldesc:
			if 'id' in col:
				column_type = col['type']
				dlrmetadatabody['mappings']['doc']['properties'][str(col['id'])] = column_types_dict[column_type]

		es.indices.create(index='dlrmetadata', body=dlrmetadatabody)

	es.indices.put_settings(index='dlrmetadata', body={'index': {"refresh_interval" : '-1'}})

	# Falls Daten schon existieren und nur upgedated werden sollen, werden sie gelöscht
	if es.indices.exists('dlrmetadata'):
		es.delete_by_query(index='dlrmetadata', doc_type='doc', body={'query': {'match': {'filename': filename}}})
	print('add document...')
	addDocument(datafile, metafile, filename, INDEX_NAME='dlrmetadata', TYPE='doc', es=es)

	metadata = json.loads(metafile.read().decode('utf-8').replace('\0', ''))
	print('check indices')
	if es.indices.exists('dataoverview'):
		es.delete_by_query(index='dataoverview', doc_type='doc', body={'query': {'match': {'filename': filename}}})
	now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
	datafile.seek(0)
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