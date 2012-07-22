#!/usr/bin/python2 -tt

import musicbrainzngs as mb

mb.set_useragent('AudioClick','0.1dev')

def request_release(releases):
	num=1
	if len(releases)==1 : return releases[0]
	print 'The track has been released in these albums:-'
	for release in releases:
		if 'date' in release:
			print str(num)+'.\t'+release['title']+'\t'+release['date']
			num+=1
			continue
		print str(num)+'.\t'+release['title']
		num+=1
	opt=int(raw_input('Enter the album no.:'))
	return releases[opt]

def extract_year(release):
	if 'date' in release.keys() : 
		year=int(release['date'].replace('-','')[:4])
	return -1

def single_recording_lookup(mbids, func=request_release):
	mbid=mbids[0]
	rec_info=mb.get_recording_by_id(mbid,['artists','releases'],['official'])['recording']
	track={}
	track['title']=rec_info['title']
	track['artist']=rec_info['artist-credit-phrase']
	track['musicbrainz_trackid']=mbid
	releases=rec_info['release-list']
	print track['artist']+' - '+track['title']							#Print in request func!
	if len(releases)==1 :
		final_release=releases[0]
	else :
		final_release=func(releases)
	track['album']=final_release['title']
	track['date']=final_release['date']
	return track

def generate_track(rec_info,final_release):
	track={}
	track['title']=rec_info['title']
	track['artist']=rec_info['artist-credit-phrase']
	track['musicbrainz_trackid']=final_release['trackid']
	track['album']=final_release['title']
	track['date']=final_release['date']
	return track

def match_recordings(mbids):
	release_list=[]
	mbid_rec={}
	for mbid in mbids:
		try:
			mbid_info=mb.get_recording_by_id(mbid,['artists','releases'],['official'])['recording']
		except mb.musicbrainz.ResponseError :
			print 'Invalid MusicBrainz Response'
			continue
		mbid_rlist=mbid_info['release-list']
		mbid_rec[mbid]=mbid_info
		for item in mbid_rlist:
			item['trackid']=mbid
		release_list.extend(mbid_rlist)
	oldest_release=find_oldest_release(release_list)
	oldest_rec=mbid_rec[oldest_release['trackid']]
	return generate_track(oldest_rec,oldest_release)

def find_oldest_release(releases):
	releases.sort(key=extract_year)
	for release in releases:
		if 'date' in release.keys() :
			return release
	
#def multiple_track_match(mbids):	
