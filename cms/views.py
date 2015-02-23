import os
import csv
from datetime import datetime, date
from cStringIO import StringIO
from PIL import Image, ImageEnhance

from django.conf import settings
from django.views.generic import View
from django.http import HttpResponse, Http404
from django.core.mail import send_mail


from bs4 import BeautifulSoup, CData

bufsize = 0 # making file unbuffered


DALY = 'daly@propertyissmo.com'
PROPPIX = 'support@prop-pix.com'

CITY_CODES = {
  'dubai':2,
  'abu dhabi':3,
  'aas al khaimeh':11,
  'sharjah':12,
  'fujeirah':13,
  'ajman':14,
  'umm al quwain':15,
  'al ain':39
				}


TYPE_SALE = ['s', 'S']
TYPE_RENT = ['r','R']
COMMERCIAL_CODES = ['RE', 'OF', 'IN', 'ST', 're', 'of', 'in', 'st']
SUBTYPE_COMMERCIAL = ['CO', 'co']
MULTIPLE_UNITS = ['BU', 'bu']
LAND_FOR_SALE = ['LA', 'la']
APARTMENT = ['ap', 'AP']
VILLA = ['vi', 'VI']

DBZ_AMENITIES = {'balcony': 'BA',
 'built in kitchen appliances': 'BK',
 'built in wardrobes': 'BW',
 'central a/c & heating': 'AC',
 'concierge service': 'CS',
 'covered parking': 'CP',
 'maid service': 'MS',
 'maids room': 'MR',
 'pets allowed': 'PA',
 'private garden': 'PG',
 'private gym': 'PY',
 'private jacuzzi': 'PJ',
 'private pool': 'PP',
 'security': 'SE',
 'shared gym': 'SY',
 'shared pool': 'SP',
 'shared spa': 'SS',
 'study': 'ST',
 'view of landmark': 'BL',
 'view of water': 'VW',
 'walk': 'WC',
 'dining in building': 'DB',
 'retail in building': 'RB',
 'available network': 'AN',
 'available furnished': 'AF',
 'conference room': 'CR',
 'furnished': 1 }


class IssmoDubizzleFull(View):
	def get(self, request, *args, **kwargs):
		return HttpResponse(open(settings.DBZ_FULL_XML).read(), content_type="text/xml; charset=utf-8")

	
class IssmoDubizzleLive(View):

	def get(self, request, *args, **kwargs):
		return HttpResponse(open(settings.DBZ_HOURLY_XML).read(), content_type="text/xml; charset=utf-8")

	def post(self, request, *args, **kwargs):
		print 'dbz got post'
		soup = BeautifulSoup(request.POST.get('<?xml version', None))
		try:
			agent_email = soup.find('email').text
		except:
			agent_email = None
		if soup is None:
			print "soup returned none"
			return Http404('Soup returned None')
		else:
			dbz_soup, errors = convert_to_dbz(soup)
			# 1. build dbz 
			if dbz_soup:
				# 2. soup feed_file
				feed_file = open(settings.DBZ_HOURLY_XML, 'rb', bufsize)
				feed_file_soup = BeautifulSoup(feed_file)
				# if not feed_file_soup.dubizzlepropertyfeed.is_empty_element:
				try:
					feed_file_soup.dubizzlepropertyfeed.unwrap()
				except:
					pass
						# 3. search for listing
				ref_no = dbz_soup.find('refno').text
				existing_listing = feed_file_soup.find('refno', text=ref_no)
				dbz_feed = dbz_soup.new_tag('dubizzlepropertyfeed')
				feed_file = open(settings.DBZ_HOURLY_XML, 'wb', bufsize)
				full_dump_file = open(settings.DBZ_FULL_XML, 'wb', bufsize)
				if existing_listing:
					print 'listing already present'
					existing_listing.parent.decompose()
					print 'removing %s' %existing_listing.parent
					feed_file_soup.append(dbz_soup)
					dbz_feed.append(feed_file_soup)
					print 'adding %s' %feed_file_soup
					feed_file.write(str(dbz_feed))
					full_dump_file.write(str(dbz_feed))

				else:
					print 'new listing'
					feed_file_soup.append(dbz_soup)
					print '%s' %dbz_soup
					dbz_feed.append(feed_file_soup)
					feed_file.write(str(dbz_feed))
					full_dump_file.write(str(dbz_feed))
				if errors:
					send_mail('%s: Successful on dubizzle' %ref_no, 'Please take care of the following \n %s' %[error for error in errors],
					 PROPPIX, [agent_email,])
				else:
					send_mail('%s: Successful on dubizzle' %ref_no, 'Listing was published without any errors', PROPPIX, [agent_email, ])
				return HttpResponse(status=201)
						#return HttpResponse(dbz_soup, content_type="application/xhtml+xml")
			else:
				try:
					ref_no = soup.find('mlsnumber').text
				except:
					ref_no = None
				send_mail('%s: Failed on dubizzle' %ref_no, '%s' %[error for error in errors], PROPPIX, [agent_email,])
				return HttpResponse(status=404)

def convert_to_dbz(soup):
		errors = []
		#soup is Beautifulsoup
		MLSNumber = soup.find('mlsnumber')

		if MLSNumber is not None:
				# varaible to use in emails. 
				_mls = MLSNumber.text.strip()
				#start by creating a parent <property> tag
				dbz_soup = BeautifulSoup('<property></property>')

				property_tag = dbz_soup.property
				#calculate the ref_no
				codes = _mls.split('-')
				if codes[0] in TYPE_RENT:
						type_tag = dbz_soup.new_tag('type')
						type_tag.append('RP')
				elif codes[0] in TYPE_SALE:
						err = "Skipping sale listing from dbz"
						errors.append(err)
						print err
						return (None, errors)
						type_tag = dbz_soup.new_tag('type')
						type_tag.append('SP')
				else:
						#log and email
						err = "%s incompatible mlsnumber" %_mls
						errors.append(err)
						print err
						return (None, errors)
				### adding type tag ### 
				property_tag.append(type_tag)
				if codes[1] in APARTMENT:
						subtype_tag = dbz_soup.new_tag('subtype')
						subtype_tag.append('AP')
				elif codes[1] in VILLA:
						subtype_tag = dbz_soup.new_tag('subtype')
						subtype_tag.append('VI')
				elif codes[1] in SUBTYPE_COMMERCIAL:
						if codes[2] not in COMMERCIAL_CODES or not codes[2]:
								err = "%s Incorrect or no commercial codes" %_mls
								errors.append(err)
								print err
								return (None, errors)
						else:
								subtype_tag = dbz_soup.new_tag('subtype')
								subtype_tag.append('CO')
								commercial_tag = dbz_soup.new_tag('commercialtype')
								commercial_tag.append(codes[2].upper())
								property_tag.append(commercial_tag)
				elif codes[1] in MULTIPLE_UNITS and codes[0] in TYPE_SALE:
						subtype_tag.new_tag('subtype')
						subtype_tag.append('BU')
				elif codes[1] in LAND_FOR_SALE and codes[0] in TYPE_SALE:
						subtype_tag.new_tag('subtype')
						subtype_tag.append('LA')
				else:
						err = 'Incorrect or missing subtype code. Wrong MLSNumber! Please check codes'
						errors.append(err)
						return (None, errors)
				### adding type tag ### 
				property_tag.append(subtype_tag)
		else:
				err = 'MLSNumber is empty'
				errors.append(err)
				return (None, errors)

		## status tag ##
		status = soup.find('listingstatus')
		if status:
			status_tag = dbz_soup.new_tag('status')
			if status.text == 'Active':
				status_tag.append('vacant')
			else:
				status_tag.append('deleted')
			property_tag.append(status_tag)
		else:
			err = "Listing status is empty. Please specify if it is active or closed."
			errors.append(err)
			return (None, errors)
			

		## ref no tag ##
		ref_no_tag = dbz_soup.new_tag('refno')
		ref_no_tag.append(_mls)
		property_tag.append(ref_no_tag)
		
		## title tag
		title_tag = dbz_soup.new_tag('title')
		title = soup.find('streetname').text
		if title:
				title_tag.append(title)
				property_tag.append(title_tag)
		else:
			err = "Title is empty. Please fill it up in Street Name."
			errors.append(err)
			return (None, errors)


		## CDATA description tag
		description_tag = dbz_soup.new_tag('description')
		description = soup.find('publicremark')
		if description:
				description = CData(description.text)
				description_tag.append(description)
				property_tag.append(description_tag)
		else: 
			err = "Listing has no description. Please fill up public remarks."
			errors.append(err)
			return (None, errors) # description is required field

		## city tag ##
		city_tag = dbz_soup.new_tag('city')
		city = soup.find('city')
		if city:
			if city.text.lower() in CITY_CODES.keys():
				city_code = CITY_CODES[city.text.lower()]
				city_tag.append(str(city_code))
				property_tag.append(city_tag)
			else:
				err = "Incorrect city name"
				errors.append(err)
				return (None, errors)
		else:
			err =  "City name is empty. Please provide one." 
			errors.append(err)
			return (None, errors)

		## size ##
		size_tag = dbz_soup.new_tag('size')
		size = soup.find('squarefeet')
		if size:
			size_tag.append(size.text)
			property_tag.append(size_tag)
		else: 
			err =  "Square feet is empty, please fill it up."
			errors.append(err)
			return (None, errors)

		## price ##
		price_tag = dbz_soup.new_tag('price')
		price = soup.find('listprice')
		if price:
				price_tag.append(price.text)
				property_tag.append(price_tag)
		else:
			err = "List price is empty"
			errors.append(err)
			return (None, errors)

		## location ##
		location_text_tag = dbz_soup.new_tag('locationtext')
		location_text = soup.find('listingarea')
		if location_text:
				location_text_tag.append(location_text.text)
				property_tag.append(location_text_tag)
		else:
			err = "Area name is empty."
			errors.append(err)
			return (None, errors)

		## building ##
		building_tag = dbz_soup.new_tag('building')
		building = soup.find('buildingfloor')
		if building.text:
			building_tag.append(building.text)
		else:
			err = "Building name is empty. Please fill buildingfloor"
			errors.append(err)
		property_tag.append(building_tag)


		## lastupdate ##
		lastupdated_tag = dbz_soup.new_tag('lastupdated')
		lastupdated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		lastupdated_tag.append(lastupdated)
		property_tag.append(lastupdated_tag)

		## contactemail ##
		email = soup.find('email')
		if email:
				email_tag = dbz_soup.new_tag('contactemail')
				email_tag.append(email.text)
				property_tag.append(email_tag)
		else:
			err = 'email is empty'
			errors.append(err)

		## contactnumber ##
		contactnumber_tag = dbz_soup.new_tag('contactnumber')
		cellphone = soup.find('cellphone')
		if cellphone:
				contactnumber_tag.append(cellphone.text)
				property_tag.append(contactnumber_tag)
		else:
			err = 'mobile number is empty'
			errors.append(err)
		## images ##

		images = soup.find_all('picture')
		if images:
				print 'calling build_images'
				image_urls = build_images(images, refno=MLSNumber.text)
				if image_urls:
						image_tag = dbz_soup.new_tag('photos')
						print 'creating image tag'
						if len(image_urls) == 1:
								image_tag.append(image_urls[0])
						if len(image_urls) > 1:
								url_string = ""
								for url in image_urls[:len(image_urls)-1]:
										url_string += url + '|'
								url_string += image_urls[-1]
								image_tag.append(url_string)
						property_tag.append(image_tag)

		
		## bedrooms ##                        
		if subtype_tag.text in VILLA or subtype_tag.text in APARTMENT:
			bedrooms = soup.find('bedrooms')
			if bedrooms:
				bedrooms_tag = dbz_soup.new_tag('bedrooms')
				if bedrooms.text != '100':
					bedrooms_tag.append(bedrooms.text)
				elif bedrooms.text == '100':
					bedrooms_tag.append('0')
				property_tag.append(bedrooms_tag)
			else:
				err = "No.of bedrooms is not provided. Please specify a number or 100 for studio"
				errors.append(err)
				return (None, errors)

		## bathrooms ##
		bathrooms = soup.find('bathtotal')
		if bathrooms:
			bathrooms_tag = dbz_soup.new_tag('bathrooms')
			bathrooms_tag.append(bathrooms.text)
			property_tag.append(bathrooms_tag)
		else:
			err = "No.of bathrooms is empty"
			errors.append(err)

		## ameneties ##
		amenities = []
		parking = soup.find('parking')
		try:
			parking_contents = parking.contents
			for content in parking_contents:
				if content.text == 'Yes':
					amenities.append('CP')
					break
		except:
			pass

		ac = soup.find('cooling')
		if ac:
			amenities.append('AC')

		features = soup.find_all('feature')
		if features:
			for feature in features:
				print '%s checking features' %_mls
				if feature.text in DBZ_AMENITIES.keys():
					if feature.text.lower() == 'furnished':
						funished_tag = dbz_soup.new_tag('furnished')
						funished_tag.append('1')
						property_tag.append(funished_tag)
					else:
						amenities.append(DBZ_AMENITIES[feature.text.lower()])
	
		print 'checking private'
		if len(amenities) == 1:
			amenities = amenities[0]
		elif len(amenities) > 1:
			amenities_string = ''
			for a in amenities[:len(amenities)-1]:
				amenities_string += a + '|'
				amenities_string += amenities[-1]
				amenities = amenities_string
		else:
			amenities = ''

		if subtype_tag.text in VILLA or subtype_tag.text in APARTMENT:
			p_amenities = dbz_soup.new_tag('privateamenities')
			print "%s :%s" %(_mls, p_amenities)
			p_amenities.append(amenities)
			property_tag.append(p_amenities)
		elif subtype_tag.text in SUBTYPE_COMMERCIAL:
			p_amenities = dbz_soup.new_tag('commercialamenities')
			print "%s :%s" %(_mls, p_amenities)
			p_amenities.append(amenities)
			property_tag.append(p_amenities)

		print 'returning soup'
		return (dbz_soup, errors)


def build_image_path(refno, imgId=None, imgCaption=None):
		print 'going in build image path'
		if imgId is not None:
				folder_path = "/%s/%s/" %(date.today(), refno)
				folder_path = folder_path.replace(' ', '_')
				print folder_path
				try:
						os.makedirs(settings.MEDIA_ROOT+folder_path)
				except Exception, e:
						print e
				paths = {
				'full_img_path' : settings.MEDIA_ROOT + folder_path + imgId,
				'media_path' : "media" + folder_path + imgId
				}

				return paths

def watermark_image(image):
	image = image.convert('RGB')
	watermark = Image.open(settings.WATERMARK).convert("RGBA")
	alpha = watermark.split()[3]
	alpha = ImageEnhance.Brightness(alpha).enhance(settings.WATERMARK_OPACITY)
	watermark.putalpha(alpha)
	layer = Image.new("RGBA", image.size, (0,0,0,0))
	#positioning in center
	watermark_position = (image.size[0]/2-watermark.size[0]/2, image.size[1]/2-watermark.size[1]/2)
	layer.paste(watermark, watermark_position)
	return Image.composite(layer, image, layer)

def build_images(images, refno):
		"""
		<picture>
		<pictureid>
		<picturecaption>
		<contentytype>
		<binarydata>
		"""
		image_urls = []
		for image in images:
				try:
					content_type = image.contenttype.text
					encoded_data = image.binarydata.string.replace(' ','+')
					decoded_data = encoded_data.decode('base64')
					print 'decoded'
					imgfile = StringIO(decoded_data)
					img = Image.open(imgfile)
					print 'image opened'
					imgId = image.pictureid.text.strip('{,}')
					imgCaption = image.picturecaption.text
					img_paths = build_image_path(refno, imgId, imgCaption)
					full_img_path = img_paths['full_img_path'] + '.' + content_type.lower()

					try:
						image_exists = open(full_img_path, 'r')
					except IOError:
						print 'watermarking image'
						img = watermark_image(img)
						print 'watermarking complete'
						print 'saving image %s' %full_img_path
						img.save(full_img_path)
						print 'save comple.'
					image_xml_url = settings.DOMAIN_NAME + img_paths['media_path'] + '.' + content_type.lower()
					image_urls.append(image_xml_url)
				except Exception,e:
						print e
						continue
		return image_urls




class IssmoPropertyFinderFull(View):
	def get(self, request, *args, **kwargs):
		return HttpResponse(open(settings.PF_FULL_XML), content_type="text/xml; charset=utf-8")


class IssmoPropertyFinderLive(View):
	def get(self, request, *args, **kwargs):
		return HttpResponse(open(settings.PF_HOURLY_XML), content_type="text/xml; charset=utf-8")

	def post(self, request, *args, **kwargs):
		print 'pf got post'
		soup = BeautifulSoup(request.POST.get('<?xml version', None))
		pf_soup = convert_to_pf(soup)
		
		if pf_soup is not None:
			pf_soup, operation = pf_soup[0], pf_soup[1]
			feed_file = open(settings.PF_HOURLY_XML, 'rb+', bufsize)
			feed_file_soup = BeautifulSoup(feed_file)
			try:
				feed_file_soup.list.unwrap()
			except AttributeError:
				pass
			
			output_feed_file = open(settings.PF_HOURLY_XML, 'wb+', bufsize)
			full_dump_file = open(settings.PF_FULL_XML, 'wb+', bufsize)

			pf_feed = pf_soup.new_tag('list')
			pf_feed.append(feed_file_soup)

			if operation == "APPEND/REPLACE":				
				reference_number = pf_soup.find('reference_number').text
			elif operation == "REMOVE":
				reference_number = pf_soup.find('mlsnumber').text
			existing_listing = feed_file_soup.find('reference_number', text=reference_number)
			if operation == "APPEND/REPLACE" and existing_listing:
				existing_listing.parent.decompose()
				feed_file_soup.append(pf_soup)
			elif operation == "REMOVE" and existing_listing:
				existing_listing.parent.decompose()
			elif operation == "APPEND/REPLACE" and not existing_listing:
				feed_file_soup.append(pf_soup)
			
			pf_feed.attrs['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			pf_feed.attrs['listing_count'] = len(pf_feed.find_all('property'))
			output_feed_file.write(str(pf_feed))
			full_dump_file.write(str(pf_feed))
			return HttpResponse(status=201)
		else:
			return Http404('pf soup returned None')

def convert_to_pf(soup):
	pf_soup = BeautifulSoup("<property last_update=''></property>")
	property_tag = pf_soup.property
	
	operation = "APPEND/REPLACE"

	#status
	status = soup.find('listingstatus')
	if status:
		if status.text != "Active":
			operation = "REMOVE"
			return (soup, operation)

	print 'status checked'

	# reference 
	reference = soup.find('mlsnumber')
	if reference:
		reference_number = reference.text
		reference_number_tag = pf_soup.new_tag('reference_number')
		reference_number_tag.append(CData(reference_number))
		property_tag.append(reference_number_tag)
	else:
		# message = "Missing reference no!"
		# if  pf_soup.find('email') is not None:
		# 	_to = pf_soup.find('email').text
		# else:
		# 	_to = DALY
		# send_mail(message, str(pf_soup), _to)
		return None

	print 'ref checked'

	#offering type
	codes = reference.text.split('-')
	if codes[0] in TYPE_RENT:
		if codes[1] in APARTMENT or codes[1] in VILLA:
			offering_type = 'RR'
		elif codes[1] in SUBTYPE_COMMERCIAL:
			offering_type = 'CR'
	elif codes[0] in TYPE_SALE:
		if codes[1] in APARTMENT or codes[1] in VILLA:
			offering_type = 'RS'
		elif codes[1] in SUBTYPE_COMMERCIAL:
			offering_type = 'CS'
	if offering_type:
		offering_type_tag = pf_soup.new_tag('offering_type')
		offering_type_tag.append(CData(offering_type))
		property_tag.append(offering_type_tag)
	else:
		return None

	# property_type
	if codes[1]:
		if codes[1] in APARTMENT:
			property_type = 'AP'
		elif codes[1] in VILLA:
			property_type = 'VH'
		elif codes[1] in SUBTYPE_COMMERCIAL:
			property_type = 'CO'
		property_type_tag = pf_soup.new_tag('property_type')
		property_type_tag.append(CData(property_type))
		property_tag.append(property_type_tag)

	print 'codes checked'

	# price
	price = soup.find('listprice')
	if price:
		price_tag = pf_soup.new_tag('price')
		price_tag.append(CData(price.text))
		property_tag.append(price_tag)
	else:
		return None
	print 'price check'
		
	#city
	city = soup.find('city')
	if city:
		city_tag = pf_soup.new_tag('city')
		city_tag.append(CData(city.text))
		property_tag.append(city_tag)

	print 'city'

	# community
	community = soup.find('listingarea')
	if community.text:
		community_tag = pf_soup.new_tag('community')
		subcommunity_tag = pf_soup.new_tag('subcommunity')
		community_tag.append(CData(community.text))
		subcommunity_tag.append(CData(community.text))
		property_tag.append(community_tag)
		property_tag.append(subcommunity_tag)

	print 'community'

	# building
	building = soup.find('buildingfloor')
	property_name_tag = pf_soup.new_tag('property_name')
	if building.text:
		property_name_tag.append(CData(building.text))
	property_tag.append(property_name_tag)

	# title
	title = soup.find('streetname')
	if title:
		title_tag = pf_soup.new_tag('title_en')
		title_tag.append(CData(title.text))
		property_tag.append(title_tag)
	else:
		return None

	# description
	description = soup.find('publicremark')
	if description:
		description_tag = pf_soup.new_tag('description_en')
		description_tag.append(CData(description.text))
		property_tag.append(description_tag)

	print 'description checked'
	# amenities
	# read from features

	# views
	# read from features

	# size
	size = soup.find('squarefeet')
	if size:
		size_tag = pf_soup.new_tag('size')
		size_tag.append(CData(size.text))
		property_tag.append(size_tag)

	# bedroom
	bedrooms = soup.find('bedrooms')
	if bedrooms:
		bedrooms_tag = pf_soup.new_tag('bedroom')
		if bedrooms.text == '100':
			bedrooms_tag.append(CData('studio'))
		else:
			bedrooms_tag.append(CData(bedrooms.text))
		property_tag.append(bedrooms_tag)

	print 'bedrooms checked'

	# bathrooms
	bathrooms = soup.find('bathtotal')
	if bathrooms:
		bathrooms_tag = pf_soup.new_tag('bathroom')
		bathrooms_tag.append(CData(bathrooms.text))
		property_tag.append(bathrooms_tag)

	# agent
	agent = soup.find('reagent')
	if agent:
		agent_tag = pf_soup.new_tag('agent')
		
		#name
		if agent.firstname:
			firstname = agent.firstname.text
		if agent.lastname:
			lastname = agent.lastname.text
		agent_name = firstname + ' ' + lastname
		agent_name_tag = pf_soup.new_tag('name')
		agent_name_tag.append(CData(agent_name))
		agent_tag.append(agent_name_tag)

		#email
		if agent.email:
			email_tag = pf_soup.new_tag('email')
			email_tag.append(CData(agent.email.text))
			agent_tag.append(email_tag)

		#phone
		if agent.cellphone:
			cellphone_tag = pf_soup.new_tag('phone')
			cellphone_tag.append(CData(agent.cellphone.text))
			agent_tag.append(cellphone_tag)

		property_tag.append(agent_tag)

	#parking
	# parking = soup.find('parking')
	# if parking:
	# 	try:
	# 		parking_contents = parking.contents
	# 		for content in parking_contents:
	# 			if content.text == 'Yes':
	# 				parking_tag = pf_soup.new_tag('parking')
	# 				parking_tag.append(CData(************))

	#furnished
	features = soup.find_all('feature')
	if features:
		for feature in features:
			if feature.text == 'Furnished':
				funished_tag = pf_soup.new_tag('furnished')
				funished_tag.append(CData('Y'))
				property_tag.append(funished_tag)
	
	print 'getting images'
	#photos
	images = soup.find_all('picture')
	if images:
		print 'going in build_images'
		image_urls = build_images(images, refno=reference_number)
		if image_urls:
			photo_tag = pf_soup.new_tag('photo')
			for url in image_urls:
				url_tag = pf_soup.new_tag('url')
				url_tag.attrs['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				url_tag.append(CData(url))
				photo_tag.append(url_tag)

			property_tag.append(photo_tag)

	property_tag.attrs['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	return (pf_soup, operation) 




class IssmoPropertyFinderLive_V2(View):
	def get(self, request, *args, **kwargs):
		return HttpResponse(open(settings.PF_HOURLY_XML_V2), content_type="text/xml; charset=utf-8")

	def post(self, request, *args, **kwargs):
		print 'pf_v2 got post'
		soup = BeautifulSoup(request.POST.get('<?xml version', None))
		pf_soup = convert_to_pf_v2(soup)

		if pf_soup[0] is not None:
			pf_soup, operation, errors = pf_soup[0], pf_soup[1], pf_soup[2]
			feed_file = open(settings.PF_HOURLY_XML_V2, 'rb+', bufsize)
			feed_file_soup = BeautifulSoup(feed_file)
			try:
				feed_file_soup.array.unwrap()
			except AttributeError:
				pass
			
			output_feed_file = open(settings.PF_HOURLY_XML_V2, 'wb+', bufsize)
			full_dump_file = open(settings.PF_FULL_XML_V2, 'wb+', bufsize)

			pf_feed = pf_soup.new_tag('array')
			pf_feed.append(feed_file_soup)

			if operation == "APPEND/REPLACE":				
				reference_number = pf_soup.find('reference').text
			elif operation == "REMOVE":
				reference_number = pf_soup.find('mlsnumber').text
			existing_listing = feed_file_soup.find('reference', text=reference_number)
			if operation == "APPEND/REPLACE" and existing_listing:
				existing_listing.parent.decompose()
				feed_file_soup.append(pf_soup)
			elif operation == "REMOVE" and existing_listing:
				existing_listing.parent.decompose()
			elif operation == "APPEND/REPLACE" and not existing_listing:
				feed_file_soup.append(pf_soup)
			
			output_feed_file.write(str(pf_feed))
			full_dump_file.write(str(pf_feed))

			try:
				agent_email = pf_soup.find('email').text
			except:
				agent_email = None

			if not errors:
				send_mail('%s: Successful on PropertyFinder' %reference_number, '%s was '
				'successful on PropertyFinder' %reference_number,
				 PROPPIX, [agent_email,])
			else:
				send_mail('%s: Successful on PropertyFinder' %reference_number, '%s was '
				'published with on PropertyFinder but has errors: \n %s' %(reference_number,[error for error in errors]),
				 PROPPIX, [agent_email,])

			return HttpResponse(status=201)
		else:
			if soup.find('mlsnumber'):
				reference_number = soup.find('mlsnumber').text
			else: reference_number = None
			send_mail('%s Listing failed to publish' %reference_number, "%s" %[error for error in pf_soup[1]], 
			PROPPIX, [agent_email, ])
			return HttpResponse(status=404)

def convert_to_pf_v2(soup):
	# messages to notify to agent
	errors = []

	pf_soup = BeautifulSoup("<listing></listing>")
	property_tag = pf_soup.listing
	
	operation = "APPEND/REPLACE"

	#status
	status = soup.find('listingstatus')
	if status:
		if status.text != "Active":
			operation = "REMOVE"
			return (soup, operation)

	print 'status checked'

	# reference 
	reference = soup.find('mlsnumber')
	if reference:
		reference_number = reference.text.strip()
		reference_number_tag = pf_soup.new_tag('reference')
		reference_number_tag.append(reference_number)
		property_tag.append(reference_number_tag)
	else:
		err = 'missing reference number'
		errors.append(err)
		print err
		return (None, errors)

	print '%s ref checked' %reference_number

	#offering type
	codes = reference_number.split('-')
	if codes[0] in TYPE_RENT:
		if codes[1] in APARTMENT or codes[1] in VILLA:
			offering_type = 'Residential for Rent'
		elif codes[1] in SUBTYPE_COMMERCIAL:
			offering_type = 'Commercial for Rent'
	elif codes[0] in TYPE_SALE:
		if codes[1] in APARTMENT or codes[1] in VILLA:
			offering_type = 'Residential for Sale'
		elif codes[1] in SUBTYPE_COMMERCIAL:
			offering_type = 'Commercial for Sale'
	try:
		offering_type_tag = pf_soup.new_tag('category')
		offering_type_tag.append(offering_type)
		property_tag.append(offering_type_tag)
	except:
		err = "%s: error in codes" %reference_number
		errors.append(err)
		print err
		return (None, errors)


#COMMERCIAL_CODES = ['RE', 'OF', 'IN', 'ST', 're', 'of', 'in', 'st']
	# property_type
	if codes[1]:
		if codes[1] in APARTMENT:
			property_type = 'Apartment'
		elif codes[1] in VILLA:
			property_type = 'Villa'
		elif codes[1] in SUBTYPE_COMMERCIAL:
			if codes[2] and codes[2] in COMMERCIAL_CODES:
				if codes[2] == 'RE':
					property_type = 'Retail'
				elif codes[2] == 'OF':
					property_type = 'Office Space'
				elif codes[2] == 'IN':
					property_type = 'Warehouse'
				elif codes[2] == 'ST':
					property_type = 'Staff Accommodation'

		property_type_tag = pf_soup.new_tag('type')
		property_type_tag.append(property_type)
		property_tag.append(property_type_tag)
	else:
		err = "%s: incorrect codes" %reference_number
		errors.append(err)
		print err
	print 'codes checked'

	# price
	price = soup.find('listprice')
	if price:
		price_tag = pf_soup.new_tag('price')
		price_tag.append(price.text)
		property_tag.append(price_tag)
	else:
		err = "error in price"
		errors.append(err)
		print err
		return (None, errors)
	print '%s price check' %reference_number
		
	#city
	city = soup.find('city')
	if city:
		if city.text.lower() in CITY_CODES.keys():
			city_tag = pf_soup.new_tag('city')
			city_tag.append(city.text)
			property_tag.append(city_tag)
		else:
			err = "incorrect city name"
			errors.append(err)
			print err
	else:
		err = "city name is missing"
		errors.append(err)
		print err
	print '%s city' %reference_number

	# community
	community = soup.find('listingarea')
	if community:
		community_tag = pf_soup.new_tag('community')
		community_tag.append(community.text)
		property_tag.append(community_tag)
	else:
		err = "No area name provided"
		errors.append(err)
		print err

	print 'community checked'

	# building & subcom
	building = soup.find('buildingfloor')
	property_name_tag = pf_soup.new_tag('property')
	subcommunity_tag = pf_soup.new_tag('subcommunity')
	if building:
		subcommunity = get_subcommunity_for_building(building.text)
		if subcommunity:
			subcommunity_tag.append(subcommunity)
		else:
			subcommunity_tag.append(building.text)
			property_name_tag.append(building.text)
			err = "Wrong building name. Please check and enter the official name." 
			errors.append(err)
			print err
	else:
		err = "No building name provided" 
		errors.append(err)
		print err
	property_tag.append(subcommunity_tag)
	property_tag.append(property_name_tag)

	# title
	title = soup.find('streetname')
	if title:
		title_tag = pf_soup.new_tag('title_en')
		title_tag.append(CData(title.text))
		property_tag.append(title_tag)
	else:
		err =  "listing has no title"
		errors.append(err)
		print err
		return (None, errors)

	# description
	description = soup.find('publicremark')
	if description:
		description_tag = pf_soup.new_tag('description_en')
		description_tag.append(CData(description.text))
		property_tag.append(description_tag)
	else:
		err = "listing has no description"
		errors.append(err)
		print err

	print 'description checked'
	# amenities
	# read from features

	# views
	# read from features

	# size
	size = soup.find('squarefeet')
	if size:
		size_tag = pf_soup.new_tag('sqft')
		size_tag.append(size.text)
		property_tag.append(size_tag)
	else:
		err = "listing has no size"
		errors.append(err)
		print err

	# bedroom
	bedrooms = soup.find('bedrooms')
	if bedrooms:
		bedrooms_tag = pf_soup.new_tag('bedroom')
		if bedrooms.text == '100':
			bedrooms_tag.append('studio')
		else:
			bedrooms_tag.append(bedrooms.text)
		property_tag.append(bedrooms_tag)
	else:
		err = 'listing has no bedrooms'
		errors.append(err)
		print err

	print '%s bedrooms checked' %reference_number

	# bathrooms
	bathrooms = soup.find('bathtotal')
	if bathrooms:
		bathrooms_tag = pf_soup.new_tag('bathroom')
		bathrooms_tag.append(CData(bathrooms.text))
		property_tag.append(bathrooms_tag)
	else:
		err = "listing has no bathrooms"
		errors.append(err)
		print err

	# agent
	agent = soup.find('reagent')
	if agent:
		
		#name
		if agent.firstname:
			firstname = agent.firstname.text
		if agent.lastname:
			lastname = agent.lastname.text
		agent_name = firstname + ' ' + lastname
		agent_name_tag = pf_soup.new_tag('agent_name')
		agent_name_tag.append(CData(agent_name))
		property_tag.append(agent_name_tag)

		#email
		if agent.email:
			email_tag = pf_soup.new_tag('agent_email')
			email_tag.append(CData(agent.email.text))
			property_tag.append(email_tag)
		else:
			err = "email is missing"
			errors.append(err)
			print err

		#phone
		if agent.cellphone:
			cellphone_tag = pf_soup.new_tag('agent_phone')
			cellphone_tag.append(CData(agent.cellphone.text))
			property_tag.append(cellphone_tag)
		else:
			err = "mobile number is missing"
			errors.append(err)
			print err

		

	#parking
	# parking = soup.find('parking')
	# if parking:
	# 	try:
	# 		parking_contents = parking.contents
	# 		for content in parking_contents:
	# 			if content.text == 'Yes':
	# 				parking_tag = pf_soup.new_tag('parking')
	# 				parking_tag.append(CData(************))

	#furnished
	features = soup.find_all('feature')
	if features:
		for feature in features:
			if feature.text == 'Furnished':
				funished_tag = pf_soup.new_tag('furnished')
				funished_tag.append(CData('Y'))
				property_tag.append(funished_tag)
	
	print 'getting images'
	#photos
	images = soup.find_all('picture')
	if images:
		print 'going in build_images'
		image_urls = build_images(images, refno=reference_number)
		if image_urls:
			for index, url in enumerate(image_urls):
				photo_tag = pf_soup.new_tag('photo_url_%s' %(index+1))
				photo_tag.append(CData(url))
				property_tag.append(photo_tag)

	
	return (pf_soup, operation, errors)

def get_subcommunity_for_building(building):
	csvfile = open(settings.PF_LOCATION_LIST, 'r')
	reader = csv.reader(csvfile)
	for row in reader:
		if row[-1] == building:
			subcommunity = row[-2]
			break
	csvfile.close()
	if subcommunity:
		return subcommunity
	else: return None