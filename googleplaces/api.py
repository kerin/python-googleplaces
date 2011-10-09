#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A wrapper for Google's Places API.

See: http://code.google.com/apis/maps/documentation/places/

Based on python-googlegeocoder by The Los Angeles Times Data Desk / Ben Welsh
https://github.com/datadesk/python-googlegeocoder
"""
import urllib
import urllib2
from decimal import Decimal

try:
    import json
except ImportError:
    import simplejson as json

PLACE_TYPES_ADD = ('accounting', 'airport', 'amusement_park', 'aquarium',
    'art_gallery', 'atm', 'bakery', 'bank', 'bar', 'beauty_salon',
    'bicycle_store', 'book_store', 'bowling_alley', 'bus_station', 'cafe',
    'campground', 'car_dealer', 'car_rental', 'car_repair', 'car_wash',
    'casino', 'cemetery', 'church', 'city_hall', 'clothing_store',
    'convenience_store', 'courthouse', 'dentist', 'department_store',
    'doctor', 'electrician', 'electronics_store', 'embassy', 'establishment',
    'finance', 'fire_station', 'florist', 'food', 'funeral_home',
    'furniture_store', 'gas_station', 'general_contractor', 'geocode',
    'grocery_or_supermarket', 'gym', 'hair_care', 'hardware_store', 'health',
    'hindu_temple', 'home_goods_store', 'hospital', 'insurance_agency',
    'jewelry_store', 'laundry', 'lawyer', 'library', 'liquor_store',
    'local_government_office', 'locksmith', 'lodging', 'meal_delivery',
    'meal_takeaway', 'mosque', 'movie_rental', 'movie_theater',
    'moving_company', 'museum', 'night_club', 'painter', 'park', 'parking',
    'pet_store', 'pharmacy', 'physiotherapist', 'place_of_worship', 'plumber',
    'police', 'post_office', 'real_estate_agency', 'restaurant',
    'roofing_contractor', 'rv_park', 'school', 'shoe_store', 'shopping_mall',
    'spa', 'stadium', 'storage', 'store', 'subway_station', 'synagogue',
    'taxi_stand', 'train_station', 'travel_agency', 'university',
    'veterinary_care', 'zoo'
)

PLACE_TYPES_MAPS = ('administrative_area_level_1',
    'administrative_area_level_2', 'administrative_area_level_3',
    'colloquial_area', 'country', 'floor', 'intersection', 'locality',
    'natural_feature', 'neighborhood', 'political', 'point_of_interest',
    'post_box', 'postal_code', 'postal_code_prefix', 'postal_town', 'premise',
    'room', 'route', 'street_address', 'street_number', 'sublocality',
    'sublocality_level_4', 'sublocality_level_5', 'sublocality_level_3',
    'sublocality_level_2', 'sublocality_level_1', 'subpremise',
    'transit_station'
)

PLACE_TYPES_SEARCH = PLACE_TYPES_ADD + PLACE_TYPES_MAPS


class GooglePlaces(object):
    """
    A wrapper for Google's Places API.
    """
    BASE_URI = 'https://maps.googleapis.com/maps/api/place/'

    def __init__(self, api_key):
        self.api_key = api_key

    def _fetch_json(self, method, get_params={}, post_data=None,
                    sensor=False):
        """
        Configure a HTTP request, fire it off and return the response.
        """
        get_params.update({
            'key': self.api_key,
            'sensor': str(sensor).lower(),
        })

        url = "%s%s/json" % (self.BASE_URI, method)
        url = "%s?%s" % (url, urllib.urlencode(get_params, doseq=True))

        if post_data:
            post_data = json.dumps(post_data)

        request = urllib2.Request(url, post_data)
        response = urllib2.urlopen(request)

        return json.loads(response.read())

    def search(self, location, radius, types=None, language=None, name=None,
                sensor=False):
        """
        Performs a Place Search, and returns a list of PlaceSearchResult
        objects.
        """
        get_params = {}

        if isinstance(location, basestring):
            raise ValueError('Location must be provided as a lat/lng pair.')
        else:
            get_params['location'] = ','.join((str(l) for l in location))

        if radius is not None:
            if not radius > 0:
                raise ValueError("Radius must be greater than zero.")
            else:
                get_params['radius'] = radius

        if types:
            if isinstance(types, basestring):
                raise ValueError('Types must be provided as a list or tuple.')
            elif any(t not in PLACE_TYPES_SEARCH for t in types):
                raise ValueError('Invalid types list supplied.')
            else:
                get_params['types'] = '|'.join(types)

        if language:
            get_params['language'] = language

        if name:
            get_params['name'] = name

        response = self._fetch_json('search', get_params, sensor=sensor)
        if response['status'] != 'OK':
            raise ValueError(response['status'])
        return [PlaceSearchResult(r) for r in response.get('results')]

    def details(self, reference, language=None, sensor=False):
        """
        Performs a Place Details lookup, and returns a list of
        PlaceDetailsResult objects.
        """
        get_params = {
            'reference': reference,
        }

        if language:
            get_params['language'] = language

        response = self._fetch_json('details', get_params, sensor=sensor)
        if response['status'] != 'OK':
            raise ValueError(response['status'])
        return PlaceDetailsResult(response.get('result'))

    def check_in(self, reference, sensor=False):
        """
        Performs a Place Check-In, and returns the response status.
        """
        post_data = {
            'reference': reference,
        }

        response = self._fetch_json('check-in', post_data=post_data,
                                    sensor=sensor)
        if response['status'] != 'OK':
            raise ValueError(response['status'])
        return True

    def add(self, location, accuracy, name, type=None, language=None,
            sensor=False):
        """
        Submits a new Place to Google Maps. New places will be immediately to
        the submitting application, but not to other applications until
        approved by Google.

        Location should be provided as a lat/lng tuple, e.g.
        (51.5150228,-0.1082299)

        The Google Places API currently only supports a single type when
        submitting, hence the 'type' kwarg rather than 'types'.
        """
        post_data = {
            'location': dict(zip(('lat', 'lng'), location)),
            'accuracy': accuracy,
            'name': name,
        }

        if type:
            if type not in PLACE_TYPES_ADD:
                raise ValueError("'%s' is not a supported Place type." % type)
            post_data['types'] = [type]

        if language:
            post_data['language'] = language

        response = self._fetch_json('add', post_data=post_data, sensor=sensor)
        if response['status'] != 'OK':
            raise ValueError(response['status'])
        return PlaceAddResult(response)

    def delete(self, reference, sensor=False):
        """
        Deletes a Place from Google Maps.

        A Place can only be deleted if:
            - It was added by the same application as is requesting its
            deletion.
            - It has not successfully passed through the Google Maps
            moderation process, and and is therefore not visible to all
            applications.

        Attempting to delete a Place that does not meet these criteria will
        return a REQUEST_DENIED status code.
        """
        post_data = {
            'reference': reference,
        }

        response = self._fetch_json('delete', post_data=post_data,
                                    sensor=sensor)
        if response['status'] != 'OK':
            raise ValueError(response['status'])
        return True


class BaseAPIObject(object):
    """
    A generic object to be returned by the API
    """
    def __init__(self, d):
        self.__dict__ = d

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.__str__())

    def __str__(self):
        return self.__unicode__().encode("utf-8")


class PlaceSearchResult(BaseAPIObject):
    """
    A Place search result item.
    """
    def __init__(self, d):
        super(PlaceSearchResult, self).__init__(d)
        self.geometry = Geometry(self.geometry)

    def __unicode__(self):
        return unicode(self.name)


class PlaceDetailsResult(PlaceSearchResult):
    """
    A Place details lookup result item.
    """
    def __init__(self, d):
        super(PlaceDetailsResult, self).__init__(d)
        self.address_components = [AddressComponent(a)
                                   for a in self.address_components]


class PlaceAddResult(BaseAPIObject):
    """
    A Place report result item.
    """
    def __unicode__(self):
        return unicode(self.id)


class AddressComponent(BaseAPIObject):
    """
    A piece of an address returned by the API

    Contains the following attributes:

        long_name: The full text description or name of the address component
            as returned by the Geocoder.

        short_name: is an abbreviated textual name for the address component,
            if available. For example, an address component for the state of
             Alaska may have a long_name of "Alaska" and a short_name of "AK"
            using the 2-letter postal abbreviation

        type: A list indicating the type(s) of the address component.
    """
    def __unicode__(self):
        return unicode(self.long_name)


class Geometry(BaseAPIObject):
    """
    A collection of geometric data about a place result.

    Contains the following attributes:

        location: The geocoded latitude and longitude as a Coordinate object.

        viewport: The recommended viewport for the returned result, returned as
            a Bounds class object.
    """
    def __init__(self, d):
        super(Geometry, self).__init__(d)

        if hasattr(self, "viewport"):
            self.viewport = Bounds(self.viewport)
        else:
            self.viewport = None

        self.location = Coordinates(self.location)

    def __repr__(self):
        return '<%s>' % self.__class__.__name__

    def __unicode__(self):
        return unicode("Geometry")


class Bounds(BaseAPIObject):
    """
    A bounding box that contains the `southwest` and `northeast` corners
    as lat/lng pairs.
    """
    def __init__(self, d):
        super(Bounds, self).__init__(d)

        self.southwest = Coordinates(self.southwest)
        self.northeast = Coordinates(self.northeast)

    def __unicode__(self):
        return unicode("(%s, %s)" % (self.southwest, self.northeast))


class Coordinates(BaseAPIObject):
    """
    A lat/lng pair.
    """
    def __init__(self, d):
        super(Coordinates, self).__init__(d)

        self.lat = Decimal(str(self.lat))
        self.lng = Decimal(str(self.lng))

    def __unicode__(self):
        return unicode("(%s, %s)" % (self.lat, self.lng))
