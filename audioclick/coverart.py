import urllib2
import xml.dom.minidom
import json

def lookup_query(query_url):
	try:
		response=urllib2.urlopen(query_url)
	except urllib2.HTTPError as e:
		if e.code is 404:
			return (1,None)
		elif e.code is 400:
			return (2,None)
	return (0,response)

def fetch_coverart_archive(release_mbid):
	query_url='http://coverartarchive.org/release/{0}'.format(release_mbid)
	(ecode,response)=lookup_query(query_url)
	if not ecode is 0:
		return(ecode,None)
	if result is []:
		return (3,None)
	result=json.loads(response.read())['images']
	img_url=result[0]['image']
	img_data=urllib2.urlopen(img_url)
	return (0,img_data)

def lookup_lastfm(release_mbid, api_key='9ffdbe28feea0fe7cb8fc25e9dd14215'):
	raw_query='http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={0}&mbid={1}'
	query_url=raw_query.format(api_key, release_mbid)
	(ecode,response)=lookup_query(query_url)
	if not ecode is 0:
		return(ecode,None)
	doc=xml.dom.minidom.parse(response)
	image_tags=doc.getElementsByTagName('image')
	for image_tag in image_tags:
		if image_tag.getAttribute('size') == 'extralarge':
			img_url=image_tag.childNodes[0].toxml()
			img_data=urllib2.urlopen(img_url).read()
			return (0,img_data)
	return(3,None)
