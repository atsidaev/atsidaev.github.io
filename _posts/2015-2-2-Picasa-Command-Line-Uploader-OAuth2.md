---
layout: post
title: Picasa command line uploader (with OAuth2 support)
---

I am a Picasa user and I'm not very happy with this. Application is terrible (and works under Wine badly) and site is not very convinient too. But I use them since storing photos in Picasa is obvious solution for any Google account holder. For a long time I used some command line uploader I found somewhere on the net, 
but since 2015 Google dropped support of ClientLogin/OAuth1 in their services, so all of the command line tools
(including even *GoogleCL* created by Google themself) stopped working.

So I created my own solution. Here is complete source code (Python 2.7) with comments. The program takes album name and path to a directory with *.jpg files as command line arguments.

Not a cool thing is that the manual steps are needed now. OAuth2 requires you to login into your account using browser.

```python
import sys, os, json
from xml.etree import ElementTree

import httplib2
from oauth2client import client
from oauth2client.client import flow_from_clientsecrets

def handle_http_status(h,c):
	if h["status"][0] != "2":  # checking that status code is 200..299
		print "Error occured! Response from Google:"
		print h
		print c
		exit(1)

# parsing command line
if len(sys.argv) < 3:
	print "Usage: upload.py \"Album Name\" /path/to/directory/with/images"
	exit(99)

album_title = sys.argv[1]
folder = sys.argv[2]

print "Creating album \"%s\" from the folder %s" % (album_title, folder)

# Generating request for Picasa (shortened example from https://developers.google.com/picasa-web/docs/2.0/developers_guide_protocol)
request = (
"<entry xmlns='http://www.w3.org/2005/Atom' xmlns:media='http://search.yahoo.com/mrss/' xmlns:gphoto='http://schemas.google.com/photos/2007'>"
"  <title type='text'>%s</title>"
"  <gphoto:access>private</gphoto:access>"
"  <category scheme='http://schemas.google.com/g/2005#kind' term='http://schemas.google.com/photos/2007#album' />"
"</entry>") % album_title

# performing semiautomatic authentication in Google

flow = client.flow_from_clientsecrets('client_secret.json',
                                      scope='https://www.googleapis.com/auth/photos https://www.googleapis.com/auth/userinfo.profile',
                                      redirect_uri='urn:ietf:wg:oauth:2.0:oob')

auth_uri = flow.step1_get_authorize_url()
print "Please visit the following URL and authenticate:"
print
print auth_uri
print
auth_code = raw_input('Enter the auth code: ')
credentials = flow.step2_exchange(auth_code)

http = credentials.authorize(httplib2.Http())

h,c = http.request("https://www.googleapis.com/oauth2/v1/userinfo", "GET");
handle_http_status(h, c)
user_id = json.loads(c)["id"].encode("ascii")  # it is unicode somehow
user_url = "https://picasaweb.google.com/data/feed/api/user/" + user_id

# post our album creation request

h,c = http.request(user_url, "POST", body = request, headers = { 'content-type':'application/atom+xml; charset=UTF-8' } )
handle_http_status(h, c)

# obtained content is XML, we need to obtain album_id from it

album = doc = ElementTree.fromstring(c)
album_id = album.find("{http://schemas.google.com/photos/2007}id").text
album_url = user_url + "/albumid/" + album_id

# Now album is created and it's edit url is known
# Let's iterate images from the specified folder and upload them

for f in os.listdir(folder):
	if f.lower().endswith(".jpg"): 
		data = open(os.path.join(folder, f), "rb").read()
		size = len(data)
		sys.stdout.write("Uploading %s (%d bytes)..." % (f, size))
		sys.stdout.flush()
		h,c = http.request(album_url, "POST", body = data, headers = { 'Content-Type': 'image/jpeg', 'Content-Length': len(data), 'Slug': f })
		handle_http_status(h, c)
		print "Success!"
	else:
		continue

print "Album uploaded"
```
