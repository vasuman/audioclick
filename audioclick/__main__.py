#!/usr/bin/python2 -tt
import mutagen
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error
from mutagen.easyid3 import EasyID3
from fingerprint import *
import coverart
import mblookup
import os
import sys
import urllib2
import logging

_version='0.1dev'
_appname='AudioClick'


#Define all tag functions here
def tag_id3(track,audiofile,img_data):	
	try:
	#Removing existing tags
		id3obj=EasyID3(audiofile)
		id3obj.delete()
	except mutagen.id3.ID3NoHeaderError:
		log.info("Adding ID3 header for file {0}".format(audiofile))
	id3obj = EasyID3()	
	for item in track.keys():
		if item in id3obj.valid_keys.keys():
			id3obj[item]=track[item]
	id3obj.save(audiofile)
	if not img_data is None:
		afile_id3=MP3(audiofile, ID3=ID3)
		try:
			afile_id3.add_tags()
		except error:
			log.info("Adding Album Art ID3 header for file {0}".format(audiofile))
		coverart_tag=APIC(encoding=3,mime='image/png',type=2,desc=u'Cover',data=img_data)
		afile_id3.tags.add(coverart_tag)
		afile_id3.save(audiofile)
	else:
		log.warning('No Album Art for for {0[album]}'.format(track))

#Add extensions and corresponding tag functions 
tag_function={'mp3':tag_id3}

def write_tags_to_file(track,audiofile,img_data):
	global tag_function
	extension=audiofile[audiofile.rindex('.')+1:].lower()
	tag_function[extension](track,audiofile,img_data)

def rename_file(track,audiofile):
	directory=os.path.dirname(audiofile)
	src=audiofile
	trackname=u"{0[artist]} - {0[title]}.{1}".format(track,audiofile[audiofile.rindex('.')+1:])
	dst=os.path.join(directory,trackname)
	os.rename(src,dst)

def tag_all_files(directory):
	global tag_function
	supported_extensions=tag_function.keys()
	afiles=[]
	files=os.listdir(directory)
	for file in files:
		if file[file.rindex('.')+1:] in supported_extensions:
			afiles.append(file)
	for afile in afiles:
		afile_abspath=os.path.abspath(os.path.join(directory,afile))
		(return_code,parsed_result)=fingerprint_file(afile_abspath)
		if return_code in (2,3):
			log.critical('Critical Error! Terminating....')
			return return_code
		tag_file(afile_abspath,parsed_result)
	return 0

def fingerprint_file(afile):
	try:
		fp=Fingerprint(afile)
	except FingerprintError as e:
		if e.errno==1:
			log.critical('Chromaprint is not installed')
		elif e.errno==2:
			log.warning('File {0} doesn\'t have a valid audio stream. Skipping...'.format(os.path.basename(afile)))
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
	#Finding best match
	best_match=max(parsed_result.mbids.keys(), key=score_key)
	mbids=parsed_result.mbids[best_match]
	log.info('File {0} matched with {1}% accuracy'.format(os.path.basename(afile),parsed_result.scores[best_match]*100))
	#Lookin up MusicBrainz database
	track,releases=mblookup.single_match(mbids)
	log.info('{0} identified as {1[title]} by {1[artist]}'.format(os.path.basename(afile), track))
	opt=raw_input("Is that right?[Y/n] : ")
	if opt in ('n','N'):
		parsed_result.mbids.pop(best_match)
		return tag_file(afile,parsed_result)
	#Fetching Cover art
	(img_ret,img_data)=coverart.lookup_lastfm(track['musicbrainz_albumid'])
	if img_ret in (1,2):
		log.critical('Problem connecting to album art server')
	elif img_ret is 3:
		log.warning('Album {0[album]} doesn\'t seem to have a cover image'.format(track))
	#Cleaning up tags and filenames
	write_tags_to_file(track,afile,img_data)
	rename_file(track,afile)
	#Success
	return 0

if __name__=='__main__':
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s:%(message)s')
	log=logging.getLogger(__name__)
	log.info('New instance started')
	directory=os.path.abspath(sys.argv[1])
	if not os.path.isdir(directory):
		afile=directory.replace('\\','')
		if not os.path.exists(afile):
			log.critical('File doesn\'t exist!! Exiting..')
			sys.exit(1)
		(return_code,parsed_result)=fingerprint_file(afile)
		if return_code in (2,3):
			log.critical('Critical Error! Terminating....')
			sys.exit(return_code)
		tag_file(afile,parsed_result)
		sys.exit(0)
	sys.exit(tag_all_files(directory))
