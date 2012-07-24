#!/usr/bin/python2 -tt

from mutagen.easyid3 import EasyID3
from fingerprint import Fingerprint,acoustid_query,AcoustidResult
import mblookup
import os
import sys
import urllib2

_version='0.1dev'
_appname='AudioClick'

supported_extensions=['mp3']

def tag_id3(track,audiofile):	
	try:
		id3obj=EasyID3(audiofile)
		id3obj.delete()
	except mutagen.easyID3.EasyID3Error:
		print "Adding ID3 header;"
	id3obj = EasyID3()	
	for item in track.keys():
		if item in id3obj.valid_keys.keys():
			id3obj[item]=track[item]
	id3obj.save(audiofile)

def write_tags_to_file(track,audiofile):
	tag_function={'mp3':tag_id3}
	extension=audiofile[-3:]
	tag_function[extension](track,audiofile)


def rename_file(track,audiofile,directory):
	src=os.path.join(directory,audiofile)
	trackname=track['artist']+' - '+track['title']+'.mp3'
	dst=os.path.join(directory,trackname)
	os.rename(src,dst)

def tag_all_files(directory):
	global supported_extensions
	afiles=[]
	files=os.listdir(directory)
	for file in files:
		if file[-3:] in supported_extensions:
			afiles.append(file)
	print afiles
	for afile in afiles:
		fp=Fingerprint(os.path.join(directory,afile))
		query=acoustid_query(fp.fingerprint,fp.duration)
		try:
			result=urllib2.urlopen(query)
		except urllib2.HTTPError:
			print 'HTTP Access Error'
		parsed_result = AcoustidResult(result)
		#Arbitrary function to extract AcoustID score
		score_key = lambda acoustid : int(parsed_result.scores[acoustid])
		parsed_result.acoustids.sort(key=score_key)
		best_match=max(parsed_result.acoustids, key=score_key)
		mbids=parsed_result.mbids[best_match]
		track=mblookup.match_recordings(mbids)
		write_tags_to_file(track,os.path.join(directory,afile))
		rename_files(track,afile,directory)
	return 0

if __name__=='__main__':
	if len(sys.argv)<2 :
		directory=os.path.abspath(os.path.curdir)
	else :
		directory=os.path.abspath(sys.argv[1])
	tag_all_files(directory)
