'''
Load data from tsv files with column description from json file to elasticsearch. Create index for data (dlrmetadata),
column descriptions (columndescription) and data table (dataoverview). Upload new data to index / update existing data.
'''

from elasticsearch import helpers, Elasticsearch
import json
import glob, os, sys
import argparse
import datetime
import pandas as pd
import numpy as np

from outlierEvenMore import timeConv, delMissesAndOutliers, markMissesAndOutliers


def getfieldnames(f, data):
	return [w.replace('.','') for w in  data['columns']]


def getConstants(f, data):
	'''
	add constants from .json file
	'''
	fieldnames = []
	values = []
	for const in data['constants']:
		fieldnames += [const['id']]
		values += [const['value']]
	const = dict(zip(fieldnames, values))
	return const


#ToDo : delete get_location since not used anymore
def get_location(row):
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


# ToDo: clean_row since not used anymore
def clean_row(row):
	for idx,item in row.iteritems():
		if type(item)==str and item.startswith("POLYGON(("):
			row[idx].replace('N(', 'N (')
		elif type(item)==str and item.startswith("POINT("):
			row[idx].replace('T(', 'T (')
		return row


def getpolygonmean(polygon):
	meanlon, meanlat = None, None
	if type(polygon) == str and polygon.startswith("POLYGON(("):
	    p = polygon.strip(')POLYGON(').split(',')
	    coords = np.array([[float(x) for x in ort.strip().split(' ')] for ort in p])
	    meanlon, meanlat = coords.mean(axis=0)
	elif type(polygon) == str and polygon.startswith("POINT("):
		meanlon, meanlat = [float(x) for x in polygon[6:-1].split(" ")]
	return [meanlon, meanlat]


def bulk_action(df, INDEX_NAME, TYPE):
	'''	Prepare generator for bulk upload
	Input:
		df: pandas dataframe
		INDEX_NAME: elasticsearch index (dlrmetadata)
		TYPE: elasticsearch document type (doc)
	'''
	for idx, row in df.iterrows():
		row = clean_row(row)
		yield {
			'_op_type': 'index',
			'_index': INDEX_NAME,
			'_id': row[0],
			'_type': TYPE,
			'_source': row.to_json()
				#'location': get_location(row)
		}


def addDocument(data, meta, filename, INDEX_NAME, TYPE, es):
	'''	Bulk upload documents to dlrmetadata index
	INPUT:
		data: opened tsc file
		meta: opened json file
		filename: string with filename
		INDEX_NAME: elasticsearch index to add data to
		TYPE: elasticsearch type for index
		es: elasticsearch version
	'''
	data.seek(0)
	meta.seek(0)
	metadata = json.loads(meta.read().decode('utf-8').replace('\0', ''))
	meta.seek(0)
	fieldnames = getfieldnames(meta, metadata)
	meta.seek(0)
	constants = getConstants(meta, metadata)
	df = pd.read_csv(data, names=fieldnames, sep='\t', low_memory=False)
	#df = timeConv(df)
	#df = markMissesAndOutliers(df)

	# add filename to match constants and data and mission0 for simple selection later on
	df['filename'] = filename
	if "mission0" in constants:
		df["mission0"] = constants["mission0"]
	print('DATA PREPARED FOR UPLOAD ....')

	for idx in df.columns:
		#column isglobal0 not only Bool type as stated in description, not clear what values mean ...
		if idx == 'isglobal0':
			df.drop(columns='isglobal0', inplace=True)
		elif type(df[idx][0]) == str and df[idx][0].startswith("POLYGON(("):
			# Elasticsearch can' handle polygon of form 'POLYGON((0 0, 0 0, 0 0, 0 0, 0 0))' therefore chenged to POINT
			df[idx] = df[idx].apply(lambda x: x.replace("POLYGON((0 0, 0 0, 0 0, 0 0, 0 0))", "POINT(0 0)") if type(x) == str else x)
			meanlong, meanlat = np.array([getpolygonmean(x) for x in df[idx]]).T
			df['polygonmeanlon'] = meanlong
			df['polygonmeanlat'] = meanlat

	# Bulk upload files and check if successful
	successid, failedid = 0, 0
	failedids = []
	for success, info in helpers.parallel_bulk(es, bulk_action(df, INDEX_NAME, TYPE),
	                                           thread_count=4, chunk_size=50, raise_on_error=True):


		successid += info['index']['_shards']['successful']
		failedid += info['index']['_shards']['failed']
		if info['index']['_shards']['failed'] > 0:
			failedids += [info['index']['_id']]
		#if not success:
		#	failed += 1
		#else:
		#	success += 1
	print(data, 'added to elasticsearch index ', INDEX_NAME, '\n',
	      'success: ', successid, 'failed: ', failedid)
	return successid, failedid, failedids


def updateFile(datafile, metafile, filename, es):
	'''
	Function is called when upload file button is clicked. Creates indexes for data (dlrmetadata), column descriptions
	(columndescription) and data table on data.html page (dataoverview). Uploads new data to index / updates existing data
	if filenames are equal.
	Input:
		datafile: .tsv file containing data
		metaflie: .json file containing datafile information, esp. column names
		filename: string with filename, since datafile and metafile are already open
		es: elasticsearch class
	'''

	# Get config files
	indexnames = json.load(open('../../elasticsearch/elconfig.json'))

	# Column description index creation or if already existsing deleted and created again

	if not es.indices.exists(indexnames['COLUMNDESCRIPTION']) or indexnames['UPDATE_COLUMNDESCRIPTION'] == 'True':
		print('Start uploading column description')
		try:
			columnDescription = json.load(open('../../data/meta/_columnDescription.json'))
			for entry in columnDescription:
				es.index(index=indexnames['COLUMNDESCRIPTION'], doc_type='doc', body=entry)
		except (FileNotFoundError, FileExistsError):
			print('_columnDescription must be located in vis_ttt/elasticseach to continue relocate file')
			sys.exit(0)


	''' Index for data from .tsv file is created if not exists. To save disk space and speed up indexing we set numer of
	shards to 1 and number of replicas to 0 as well as polygon precision set to 100km. For polygons ignore_malformed
	is necessary since some polygons are not well defined.
	Disk space required for polygon depending on precision (original file size: 2mB):
	precision 100 km : 5 mb
	precision  10 km : 27 mb
	precision   1 km : too much (1117 docs.count: 375mb)
	'''
	print('STARTED WITH ', filename, ' ....')

	# Create index for data if not exists
	if not es.indices.exists(indexnames['DATA']):
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
				"type": "text" #if polygones are not used they could be uploaded as string
				#"type": "geo_shape",
				#"precision": "100km",
				#"ignore_malformed": True
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

		# Insert column description depending on type into mappings
		coldesc = json.load(open('../../elasticsearch/_columnDescription.json'))
		for col in coldesc:
			if 'id' in col:
				column_type = col['type']
				dlrmetadatabody['mappings']['doc']['properties'][str(col['id'])] = column_types_dict[column_type]
		es.indices.create(index=indexnames['DATA'], body=dlrmetadatabody)
		print('DLRMETADATA INDEX CREATED ....')

	# Index exists or was created, not set vriables for speed up
	#es.indices.put_settings(index='dlrmetadata', body={'index': {"refresh_interval" : '-1'}})

	# If file is updated, delete old data
	if es.indices.exists(indexnames['DATA']):
		es.delete_by_query(index=indexnames['DATA'], doc_type='doc', body={'query': {'match': {'filename': filename}}})
		print('OLD DOCUMENTS DELETED ....')

	# Upload new documents
	print('START INDEXING TO DLRMETADATA ....')
	success, failed, failedids = addDocument(datafile, metafile, filename, INDEX_NAME=indexnames['DATA'], TYPE='doc', es=es)

	# Now update data overview
	metadata = json.loads(metafile.read().decode('utf-8').replace('\0', ''))
	datafile.seek(0)

	# Delete data from table if exists
	if es.indices.exists(indexnames['DATAOVERVIEW']):
		es.delete_by_query(index=indexnames['DATAOVERVIEW'], doc_type='doc', body={'query': {'match': {'filename': filename}}})

	# Create metadata about filename
	now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
	constants = getConstants(metafile, metadata)
	filenames = {'filename': filename.split('.')[0],
	             'size': len(datafile.read()),
	             'addDate': now,
	             'updateDate': now,
	             'success': success,
	             'failed': failed,
	             'failedids': failedids}
	filenames.update(constants)
	es.index(index=indexnames['DATAOVERVIEW'], doc_type='doc', body=filenames)
	print('ADDED ', filenames['filename'], ' TO DATAOVERVIEW ....')

	print('FINISHED ', filename, '....')


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
