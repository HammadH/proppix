from datetime import datetime, date
from cStringIO import StringIO
from PIL import Image

from django.conf import settings
from django.views.generic import View
from django.http import HttpResponse, Http404

from bs4 import BeautifulSoup, CData

bufsize = 0 # making file unbuffered



class Dubizzle(View):
	
	def get(self, request, *args, **kwargs):
		return HttpResponse(open('/home/dubizzle/test_feed_file.xml').read())

	def post(self, request, *args, **kwargs):

		soup = BeautifulSoup(request.POST.get('<?xml version', None))
		

		if soup is None:
			print "soup returned none"
			return Http404('Soup returned None')
		else:

			# 1. build dbz 
			dbz_soup = convert_to_dbz(soup)
			
			# 2. soup feed_file
			feed_file = open('/home/dubizzle/test_feed_file.xml', 'rb', bufsize)
			
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
			feed_file = open('/home/dubizzle/test_feed_file.xml', 'wb', bufsize)
			if existing_listing:
				existing_listing.parent.decompose()
				feed_file_soup.append(dbz_soup)
				dbz_feed.append(feed_file_soup)
				feed_file.write(str(dbz_feed))
			else:
				feed_file_soup.append(dbz_soup)
				dbz_feed.append(feed_file_soup)
				feed_file.write(str(dbz_feed))
			
			return HttpResponse(status=201)
			#return HttpResponse(dbz_soup, content_type="application/xhtml+xml")
		 
		
DOMAIN_NAME = "www.prop-pix.com/"



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

def convert_to_dbz(soup):
	#soup is Beautifulsoup
	MLSNumber = soup.find('mlsnumber')
	if MLSNumber is not None:
		#start by creating a parent <property> tag
		dbz_soup = BeautifulSoup('<property></property>')
		
		property_tag = dbz_soup.property
		#calculate the ref_no
		codes = MLSNumber.text.split('-')
		if codes[0] in TYPE_RENT:
			type_tag = dbz_soup.new_tag('type')
			type_tag.append('RP')
		elif codes[0] in TYPE_SALE:
			type_tag = dbz_soup.new_tag('type')
			type_tag.append('SP')
		else:
			#log and email
			print "incompatible mlsnumber"
			return None
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
				print "commercial codes"
				return None
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
			print 'subtype'
			return None
		### adding type tag ### 
		property_tag.append(subtype_tag)
	else:
		print 'MLSNumber is empty'
		return None
	## status tag ##
	status = soup.find('listingstatus').text
	status_tag = dbz_soup.new_tag('status')
	if status == 'Active':
		status_tag.append('vacant')
	else:
		status_tag.append('deleted')
	property_tag.append(status_tag)
	## ref no tag ##
	ref_no_tag = dbz_soup.new_tag('refno')
	ref_no_tag.append(MLSNumber.text)
	property_tag.append(ref_no_tag)
	## title tag
	title_tag = dbz_soup.new_tag('title')
	title = soup.find('streetname').text
	if title:
		title_tag.append(title)
		property_tag.append(title_tag)


	## CDATA description tag
	description_tag = dbz_soup.new_tag('description')
	description = soup.find('publicremark')
	if description:
		description = CData(description.text)
		description_tag.append(description)
		property_tag.append(description_tag)

	## city tag ##
	city_tag = dbz_soup.new_tag('city')
	city = soup.find('city')
	if city:
		city = city.text
		city = city.lower()
		city_code = CITY_CODES[city]
		city_tag.append(str(city_code))
		property_tag.append(city_tag)

	## size ##
	size_tag = dbz_soup.new_tag('size')
	size = soup.find('squarefeet')
	if size:
		size_value = size.text
		size_tag.append(size_value)
		property_tag.append(size_tag)

	## price ##
	price_tag = dbz_soup.new_tag('price')
	price = soup.find('listprice')
	if price:
		price_tag.append(price.text)
		property_tag.append(price_tag)

	## location ##
	location_text_tag = dbz_soup.new_tag('locationtext')
	location_text = soup.find('listingarea')
	if location_text:
		location_text_tag.append(location_text.text)
		property_tag.append(location_text_tag)

	## building ##
	building_tag = dbz_soup.new_tag('building') 
	building = soup.find('buildingfloor')
	if building:
		building_tag.append(building.text)
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

	## contactnumber ##
	contactnumber_tag = dbz_soup.new_tag('contactnumber')
	cellphone = soup.find('cellphone')
	if cellphone:
		contactnumber_tag.append(cellphone.text)
		property_tag.append(contactnumber_tag)

	## images ##
	
	images = soup.find_all('picture')
	if images:
		image_urls = build_images(images, refno=MLSNumber.text)
		if image_urls:
			image_tag = dbz_soup.new_tag('photos')
			if len(image_urls) == 1:
				image_tag.append(image_urls[0])
			if len(image_urls) > 1:
				url_string = ""
				for url in image_urls[:len(image_urls)-1]:
					url_string += url + '|'
				url_string += image_urls[-1]
				image_tag.appned(url_string)
			property_tag.append(image_tag)

	bedrooms = soup.find('bedrooms')
	if bedrooms:
		bedrooms_tag = dbz_soup.new_tag('bedrooms')
		bedrooms_tag.append(bedrooms.text)
		property_tag.append(bedrooms_tag)

	
	return dbz_soup


def build_image_path(refno, imgId=None, imgCaption=None):

	if imgId is not None:
		folder_path = "/%s/%s/" %(date.today(), refno)
		folder_path = folder_path.replace(' ', '_')
		try:
			os.makedirs('media'+folder_path)
		except OSError:
			pass
		paths = {
		'full_img_path' : settings.MEDIA_ROOT[0] + folder_path + imgId,
		'media_path' : "media" + folder_path + imgId
		}
		
		return paths


def build_images(images, refno):
	"""
	<picture>
	<pictureid>
	<picturecaption>
	<contentytype>
	<binarydata>
	"""
	image_urls = []
	import pdb;pdb.set_trace()
	for image in images:
		try:
			content_type = image.contenttype.text
			encoded_data = image.binarydata.text
			decoded_data = encoded_data.decode('base64')
			imgfile = StringIO(decoded_data)
			img = Image.open(imgfile)
			imgId = image.pictureid.text.strip('{,}')
			imgCaption = image.picturecaption.text
			img_paths = build_image_path(refno, imgId, imgCaption)
			full_img_path = img_paths['full_img_path'] + '.' + content_type.lower()
			try:
				img.save(full_img_path)
				image_xml_url = DOMAIN_NAME + img_paths['media_path'] + '.' + content_type.lower()
				image_urls.append(image_xml_url)
			except Exception, e:
				continue
		except:
			continue
	return image_urls