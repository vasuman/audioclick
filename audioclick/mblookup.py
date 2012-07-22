#!/usr/bin/python2 -tt

import musicbrainzngs as mb

mb.set_useragent('AudioClick','0.1dev')

def extract_year(release):
	if 'date' in release.keys() : 
		year=int(release['date'].replace('-','')[:4])
	return -1

def find_oldest_release(releases):
	releases.sort(key=extract_year)
	for release in releases:
		if 'date' in release.keys() :
			return release
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

	
#def multiple_track_match(mbids):	
