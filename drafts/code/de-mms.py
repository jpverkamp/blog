from messaging.mms.message import MMSMessage

messages = []

def maybe_mkdir(dir):
	try:
		os.mkdir(dir)
	except:
		pass

def decode_mms(filename):
	mms = MMSMessage.from_file(filename)

	mms_from = mms.headers.get('From', '???')
	mms_to = mms.headers.get('To')
	mms_date = str(mms.headers.get('Date', '???'))
	mms_text = ''
	mms_images = []
	mms_videos = []

	for dp in mms.data_parts:
		if dp.content_type == 'text/plain':
			mms_text += dp.data
		elif dp.content_type == 'image/jpeg':
			mms_images.append(dp.data)
		elif dp.content_type == 'video/3gpp':
			mms_videos.append(dp.data)
		elif dp.content_type == 'application/smil':
			pass
		else:
			print filename
			print dp.content_type
			raw_input()

	if mms_text or mms_images or mms_videos:
		messages.append((mms_date, mms_from, mms_to, mms_text, mms_images, mms_videos))

filenames = os.listdir('messaging')
for i, file in enumerate(filenames):
	if i % 50 == 0:
		print '%d/%d' % (i, len(filenames))

	if not file[-4:] == '.mpb':
		continue

	decode_mms(os.path.join('messaging', file))

maybe_mkdir('mms_output')
maybe_mkdir(os.path.join('mms_output', 'images'))
maybe_mkdir(os.path.join('mms_output', 'videos'))
with open(os.path.join('mms_output', 'messages.htm'), 'w') as f:
	for i, message in enumerate(sorted(messages)):
		mms_date, mms_from, mms_to, mms_text, mms_images, mms_videos = message

		if i != 0:
			f.write('<br /><hr /><br />\n')
		f.write('<u>Message %04d</u><br />\n' % (i + 1))
		f.write('<pre>')
		f.write('From: %s\n' % mms_from)
		f.write('  To: %s\n' % mms_to)
		f.write('Date: %s\n' % mms_date)
		f.write('\n</pre>\n')

		if mms_text:
			f.write(mms_text)
			f.write('<br />\n')
			f.write('<br />\n')

		for j, img_data in enumerate(mms_images):
			img_filename = '%04d_%02d.jpg' % (i, j)
			with open(os.path.join('mms_output', 'images', img_filename), 'wb') as img_f:
				img_f.write(img_data)
			f.write('<a href="%s"><img width="200px" src="%s" /></a><br />\n' % (os.path.join('images', img_filename), os.path.join('images', img_filename)))

		for j, vid_data in enumerate(mms_videos):
			vid_filename = '%04d_%02d.jpg' % (i, j)
			with open(os.path.join('mms_output', 'videos', vid_filename), 'wb') as vid_f:
				vid_f.write(vid_data)
			f.write('<a href="%s">video attachment</a><br />\n' % vid_filename)
