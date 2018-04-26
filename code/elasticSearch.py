'''
script to load tsv files with column description in json file
'''

from elasticsearch import helpers, Elasticsearch
import csv, json
import glob, os
import argparse

def getfieldnames(file):
	with open(file) as f:
		data = json.load(f)
		return(tuple(data['columns']))

def getConstants(file):
	with open(file) as f:
		fieldnames = []
		values = []
		data = json.load(f)
		for const in data['constants']:
			fieldnames += [const['id']]
			values += [const['value']]
		const = dict(zip(fieldnames, values))
	return const

def addDocument(data, meta, INDEX_NAME, TYPE):
	with open(data) as f:
		fieldnames = getfieldnames(meta)
		constants = getConstants(meta)
		reader = csv.DictReader(f, fieldnames=fieldnames, delimiter='\t')
		#helpers.bulk(es, reader, index=INDEX_NAME, doc_type=TYPE)
		print('Adding documents to ' + INDEX_NAME + '/' + TYPE)
		i = 0
		for row in reader:
			row.update(constants)
			es.index(index=INDEX_NAME, doc_type=TYPE, body=row)
			i += 1
	print(data, 'added to elasticsearch index ', INDEX_NAME)

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='Create index and load tsv file in elaseicsearch.')
	parser.add_argument('--data', help='tsv file to parse')
	parser.add_argument('--meta', help='Metadata for tsv file')
	parser.add_argument('--folder', help='folder containing all files (.tsv) to upload. Metadata and data should be in '
	                                     'same folder vis_ttt/data/meta and vis_ttt/data/data')
	parser.add_argument('--INDEX_NAME', default='dlrmetadata',
	                    help='elasticsearch index name to which document will be added')
	args = parser.parse_args()

	#meta = 'data/meta/m_airrsgtc.json' #data = 'data/data/m_airrsgtc.tsv'

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
			TYPE = meta[-1].split('.')[0]
			meta[-2] = 'meta'
			meta[-1] = meta[-1].replace('.tsv', '.json')
			meta = '/'.join(meta)
			addDocument(data=data, meta=meta, INDEX_NAME= args.INDEX_NAME, TYPE=TYPE)
	else:
		TYPE = args.meta.split('/')[-1].split('.')[0]
		addDocument(data=args.data, meta=args.meta, INDEX_NAME=args.INDEX_NAME, TYPE=TYPE)