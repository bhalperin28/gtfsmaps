import io
import requests
import sys

from csv import DictReader
from polyline import encode
from natsort import natsorted
from zipfile import ZipFile

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
SF_511_API_KEY = os.environ['SF_511_API_KEY']
GTFS_URL = 'http://api.511.org/transit/datafeeds?&operator_id=SF&api_key=' + SF_511_API_KEY

if len(sys.argv) != 2:
	exit("Usage: python shapes.py [output_dir]")
outputDir = sys.argv[1]

routeShapeIds = {}
shapes = {}

# Download the Muni GTFS feed from the 511 API
gtfsData = requests.get(GTFS_URL).content

# Unzip the GTFS feed (in memory)
with io.BytesIO(gtfsData) as gtfsBytesIO:
	with ZipFile(io.BytesIO(gtfsData)) as myzip:

		# Read in from trips.txt and build a map from the route ID to a set of shape IDs
		with myzip.open('trips.txt') as tripsfile:
			tripsreader = DictReader(io.TextIOWrapper(buffer=tripsfile, encoding='utf-8'))
			for row in tripsreader:
				if row['route_id'] not in routeShapeIds:
					routeShapeIds[row['route_id']] = set()
				routeShapeIds[row['route_id']].add(row['shape_id'])

		# Read in from shapes.txt and build a map from the shape ID to a list of (lat, long) tuples
		with myzip.open('shapes.txt') as shapesfile:
			shapesreader = DictReader(io.TextIOWrapper(buffer=shapesfile, encoding='utf-8'))
			for row in shapesreader:
				if row['shape_id'] not in shapes:
					shapes[row['shape_id']] = []
				shapes[row['shape_id']].append((float(row['shape_pt_lat']), float(row['shape_pt_lon'])))

# For each route, download a map using the Google Maps Static API with the paths overlaid
for routeId in natsorted(routeShapeIds.keys()):
	paths = map(lambda shapeId: '&path=color:0xff0000ff|weight:3|enc:' + encode(shapes[shapeId]), routeShapeIds[routeId])
	map_url = 'https://maps.googleapis.com/maps/api/staticmap?style=feature:poi|visibility:off&style=feature:poi.park|visibility:on&size=1280x1280&scale=2&key=' + GOOGLE_API_KEY + ''.join(paths)

	img_data = requests.get(map_url).content
	with open(outputDir + '/' + routeId + '.png', 'wb') as handler:
		print(routeId)
		handler.write(img_data)
