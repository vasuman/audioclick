#!/usr/bin/python2 -tt

import sys
import subprocess as sbp 
import urllib2 
import json

class FingerprintError(Exception):
	'''Implements better exception handling with fpcalc tool'''
	def __init__(self,errno,msg):
		self.errno=errno
		self.msg=msg
	
	def __str__(self):
		return "{0} : {1}".format(self.errno,self.msg)

class Fingerprint(object):
	'''Object that calls the fpcalc command line tool on given audio file'''
	def __init__(self, filename):
		(self.fingerprint, self.duration)= self.fpcalc(filename)
	
	def fpcalc(self, filename):
		try:
			fpproc=sbp.Popen(['fpcalc',filename], stdout=sbp.PIPE, stderr=sbp.PIPE)
		except OSError as e:
			if e.errno==2:
				raise FingerprintError(1,'Chromaprint not found')
		(opstr,operr)=fpproc.communicate()
		opstr=opstr.split('\n')
		if operr!='' :
			if operr.split('\n')[0]=="ERROR: couldn't find any audio stream in the file":
				raise FingerprintError(2,'Invalid audio source')
		fingerprint=opstr[-2][opstr[-2].index('=')+1:]
		duration=opstr[-3][opstr[-3].index('=')+1:]
		return (fingerprint, duration)
		
def acoustid_query(fingerprint, duration, meta='recordingids', apikey='8XaBELgH'):
	'''Generates an AcoustID query'''
	fpquery='http://api.acoustid.org/v2/lookup?client={0}&meta={1}&duration={2}&fingerprint={3}'.format(apikey,meta,duration,fingerprint)
	return fpquery

class AcoustidResult(object):
	'''Object parses the AcoustID server JSON response'''
	def __init__(self, result):
		parsedresult=json.loads(result.read())
		self.status=parsedresult['status'] 
		self.scores={}
		self.mbids={}
		self.acoustids=[]
		for item in parsedresult['results']:
			self.acoustids.append(item['id'])
			self.scores[item['id']]=item['score']
			if 'recordings' in item.keys():
				recordings = item['recordings']
				mbids=[]
				for recording in recordings:
					mbids.append(recording['id'])
				self.mbids[item['id']]=mbids


#Can be run for debugging : prints AcoustIDs and associated MBIDs to stdout
if __name__=='__main__':
	fp=Fingerprint(sys.argv[1])
	query=acoustid_query(fp.fingerprint,fp.duration)
	result=urllib2.urlopen(query)
	parsed_result = AcoustidResult(result)
	print 'Matching AcoustIDs:'
	for acoustid in parsed_result.acoustids:
		print acoustid+' : '+str(parsed_result.scores[acoustid])
	print 'Associated MusicBrainzIDs:'
	for acoustid in parsed_result.mbids.keys():
		print acoustid
		for mbid in parsed_result.mbids[acoustid]:
			print '\t'+mbid
