---
title: Determining country by latitude/longitude
date: 2012-10-25 14:00:59
programming/languages:
- Python
slug: determining-country-by-latitudelongitude
---
[Yesterday]({{< ref "2012-10-24-determining-country-by-ip.md" >}}) I talked about how I used [censorship research]({{< ref "2012-08-06-usenix-foci-2012.md" >}})) where the API will report longitude and latitude but not always country.

<!--more-->

To solve this problem, I decided to make use of the <a title="Google Maps API" href="https://developers.google.com/maps/">Google Maps API</a>, specifically the <a title="Google Maps API: Geocoding" href="https://developers.google.com/maps/documentation/geocoding/">subset of the API</a> that deals with {{< wikipedia "geocoding" >}}. You can look through the specifics easily enough, but the general idea is just to use a specific URL:

<a title="Example Google Maps Geocoding API" href="http://maps.googleapis.com/maps/api/geocode/json?latlng=39.16554,-86.523525&amp;sensor=false">`http://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&amp;sensor=false`</a>

The result will be a json encoded list of results, each of which can have one or more `address_components`. Those can be all sorts of things--routes, political regions, countries, buildings; all sorts. Long story short, for this project, we're looking for a country. As soon as we find one, return it.

Luckily, Python makes fetching urls and dealing with json really straight forward:

```python
# Get a country from a latitude and longitude
def lookup(lat, lon):
	data = json.load(urllib2.urlopen('http://maps.googleapis.com/maps/api/geocode/json?latlng=%s,%s&amp;sensor=false' % (lat, lon)))

	for result in data['results']:
		for component in result['address_components']:
			if 'country' in component['types']:
				return component['long_name']

	return None
```

Trying it out:

```python
>>> lookup(39.16554,-86.523525)
u'United States'
```

And that's all there is to it. You can map this over much larger lists of latitudes and longitudes, although if you abuse it, expect to be rate limited.