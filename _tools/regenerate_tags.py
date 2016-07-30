#!/usr/bin/python

import os
import re
import shutil

posts_dir = "_posts"
tags_dir = "tag"

# cleaning target directory from any previous versions
for dname in os.listdir(tags_dir):
	shutil.rmtree(os.path.join(tags_dir, dname))

for fname in os.listdir(posts_dir):
	with open(os.path.join(posts_dir, fname)) as f:
		content = f.readlines()
	
	boundaries = 0
	i = 0
	while True:
		if content[i].startswith("---"):
			boundaries = boundaries + 1
		if boundaries == 2: # both "---" found, so nothing interest left in the file
			break

		# check current line contains tags
		m = re.match(r"[Tt]ags: \[([^\]]+)\]", content[i])
		if m:
			tags = map(lambda x: x.strip(), m.group(1).split(","))
			for tag in tags:
				tag_dir = os.path.join(tags_dir, tag)
				if not os.path.isdir(tag_dir):
					os.mkdir(tag_dir)
					with open(os.path.join(tag_dir, "index.md"), 'w') as f:
						f.write("---\n")
						f.write("layout: blog_by_tag\n")
						f.write("tag: %s\n" % tag)
						f.write("permalink: /%s/\n" % tag)
						f.write("---\n")
		i = i + 1

