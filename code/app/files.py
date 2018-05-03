import datetime
import glob
import os
import collections

def files():
	now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
	files = glob.glob(os.path.join('../data/data/', '*'))

	filenames = {}
	for data in files:
		f = data.split('/')[-1]
		filenames[f] = now

	orderedfilenames = collections.OrderedDict(sorted(filenames.items()))
	return orderedfilenames