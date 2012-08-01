
import urllib2
import json
import musicbrainzngs as mb
import logging

mb.set_useragent('AudioClick','0.1dev')

def generate_track(rec_info,final_release):
	track={}
	track['title']=rec_info['title']
	track['artist']=rec_info['artist-credit-phrase']
	track['musicbrainz_trackid']=final_release['trackid']
	track['album']=final_release['title'].encode('ascii','ignore')
	track['date']=final_release['date']
	logging.debug(final_release.keys())
	track['musicbrainz_albumid']=final_release['id']
	return track


def extract_year(release):
	if 'date' in release.keys() : 
		year=int(release['date'].replace('-',''))
		if len(release['date'])==4:
			year=int(release['date']+'1231')
		return year
	return -1

def find_oldest_release(releases):
	releases.sort(key=extract_year)
	for release in releases:
		if 'date' in release.keys() and release['status']=='Official':
			return release

def single_match(mbids):
	(mbid_rec, release_list)=match_recording(mbids)
	oldest_release=find_oldest_release(release_list)
	oldest_rec=mbid_rec[oldest_release['trackid']]
	return generate_track(oldest_rec,oldest_release)

def match_recording(mbids):
	release_list=[]
	mbid_rec={}
	for mbid in mbids:
		try:
			mbid_info=mb.get_recording_by_id(mbid,['artists','releases'],['official'])['recording']
		except mb.musicbrainz.ResponseError :
			logging.warning('{0} is an invalid MusicBrainz ID. Skipping...'.format(mbid))
			continue
		mbid_rlist=mbid_info['release-list']
		mbid_rec[mbid]=mbid_info
		for item in mbid_rlist:
			item['trackid']=mbid
		release_list.extend(mbid_rlist)
	return (mbid_rec, release_list)

#Yet to be implemented
def album_match(tracked_mbids):
	all_releases=[]
	album_match={}
	for mbids in tracked_mbids:
		(mbid_rec, release_list)=match_recording(mbids)
		all_releases.extend(release_list)
		for item in release_list:
			if not item['id'] in album_match:
				album_match[item['id']]=1
				continue
			album_match[item['id']]+=1
	match_score=lambda item: album_match[item]
	final_album=max(album_match, key=match_score)
	print final_album
	for item in all_releases:
		if final_album['id']==item['id']:
			print item
