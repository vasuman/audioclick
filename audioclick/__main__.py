#!/usr/bin/python2 -tt

import mutagen
from mutagen.easyid3 import EasyID3
from fingerprint import *
import mblookup
import os
import sys
import urllib2
import logging

_version='0.1dev'
_appname='AudioClick'


#Define all tag functions here
def tag_id3(track,audiofile):	
	try:
		id3obj=EasyID3(audiofile)
		id3obj.delete()
	except mutagen.id3.ID3NoHeaderError:
		log.info("Adding ID3 header for file {0}".format(audiofile))
	id3obj = EasyID3()	
	for item in track.keys():
		if item in id3obj.valid_keys.keys():
			id3obj[item]=track[item]
	id3obj.save(audiofile)

#Add extensions and corresponding tag functions 
tag_function={'mp3':tag_id3}

def write_tags_to_file(track,audiofile):
	global tag_function
	extension=audiofile[-3:].lower()
	tag_function[extension](track,audiofile)

def rename_file(track,audiofile):
	directory=os.path.dirname(audiofile)
	src=audiofile
	trackname=u'{0} - {1}.{2}'.format(track['artist'],track['title'],audiofile[-3:].lower())
	dst=os.path.join(directory,trackname)
	os.rename(src,dst)

def tag_all_files(directory):
	global tag_function
	supported_extensions=tag_function.keys()
	afiles=[]
	files=os.listdir(directory)
	for file in files:
		if file[-3:] in supported_extensions:
			afiles.append(file)
	for afile in afiles:
		afile_abspath=os.path.abspath(os.path.join(directory,afile))
		(return_code,parsed_result)=fingerprint_file(afile_abspath)
		if return_code in (2,3):
			log.critical('Critical Error! Terminating....')
			return
		tag_file(afile_abspath,parsed_result)

def fingerprint_file(afile):
	try:
		fp=Fingerprint(afile)
	except FingerprintError as e:
		if e.errno==1:
			log.critical('Chromaprint is not installed')
		elif e.errno==2:
			log.warning('File {0} doesn\'t have a valid audio stream. Skipping...'.format(afile))
			return (1,None)
	query=acoustid_query(fp.fingerprint,fp.duration)
	try:
		result=urllib2.urlopen(query)
	except urllib2.HTTPError as e:
		if e.code==401:
			log.error('HTTP Authentication Error. Invalid API key. Exiting...')
			return (2,None)
	except urllib2.URLError as e:
		if e.args[0][0]==-2:
			log.error('Unable to resolve hostname. Check internet connection. Exiting...')
			return (3,None)
	#Parsing JSON result from server
	parsed_result = AcoustidResult(result)
	return (0,parsed_result)

def tag_file(afile,parsed_result):
	if parsed_result.mbids=={}:
		log.warning('Track : {0} doesn\'t have an MBID. Skipping...'.format(os.path.basename(afile)))
		return 1
	#Arbitrary function to extract AcoustID score
	score_key = lambda acoustid : int(parsed_result.scores[acoustid])
	#Ranking according to AcoustID score
	parsed_result.acoustids.sort(key=score_key)
	#Finding best match
	print parsed_result.scores
	best_match=max(parsed_result.mbids.keys(), key=score_key)
	mbids=parsed_result.mbids[best_match]
	log.info('File {0} matched with {1}% accuracy'.format(os.path.basename(afile),parsed_result.scores[best_match]*100))
	#Lookin up MusicBrainz database
	track=mblookup.single_match(mbids)
	#Cleaning up tags and filenames
	write_tags_to_file(track,afile)
	rename_file(track,afile)
	#Success
	return 0

if __name__=='__main__':
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s:%(message)s')
	log=logging.getLogger(__name__)
	log.info('New instance started')
	directory=os.path.abspath(sys.argv[1])
	tag_all_files(directory)
