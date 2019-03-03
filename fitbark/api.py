# -*- coding: utf-8 -*-
import datetime
import json

import requests

try:
    from urllib.parse import urlencode
except ImportError:
    # Python 2.x
    from urllib import urlencode

from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session

from . import exceptions


class FitBarkOauth2Client(object):
    API_ENDPOINT = "https://app.fitbark.com/api"
    AUTHORIZE_ENDPOINT = "https://app.fitbark.com"
    API_VERSION = 2

    request_token_url = "%s/oauth/token" % AUTHORIZE_ENDPOINT
    authorization_url = "%s/oauth/authorize" % AUTHORIZE_ENDPOINT
    access_token_url = request_token_url
    refresh_token_url = request_token_url

    def __init__(self, client_id, client_secret, access_token=None,
                 refresh_token=None, expires_at=None, refresh_cb=None,
                 redirect_uri=None, *args, **kwargs):
        """
        Create a FitBarkOauth2Client object. Specify the first 7 parameters if
        you have them to access user data. Specify just the first 2 parameters
        to start the setup for user authorization (as an example see gather_key_oauth2.py)
        """

        self.client_id, self.client_secret = client_id, client_secret
        token = {}
        if access_token and refresh_token:
            token.update({
                'access_token': access_token,
                'refresh_token': refresh_token
            })
        if expires_at:
            token['expires_at'] = expires_at
        self.session = OAuth2Session(
            client_id,
            auto_refresh_url=self.refresh_token_url,
            token_updater=refresh_cb,
            token=token,
            redirect_uri=redirect_uri,
        )
        self.timeout = kwargs.get("timeout", None)

    def _request(self, method, url, **kwargs):
        """
        A simple wrapper around requests.
        """
        if self.timeout is not None and 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        try:
            response = self.session.request(method, url, **kwargs)

            # If our current token has no expires_at, or something manages to slip
            # through that check
            if response.status_code == 401:
                d = json.loads(response.content.decode('utf8'))
                if d['errors'][0]['errorType'] == 'expired_token':
                    self.refresh_token()
                    response = self.session.request(method, url, **kwargs)

            return response
        except requests.Timeout as e:
            raise exceptions.Timeout(*e.args)

    def make_request(self, url, data=None, method=None, **kwargs):
        """
        Builds and makes the OAuth2 Request, catches errors

        https://www.fitbark.com/dev/
        """
        data = data or {}
        method = method or ('POST' if data else 'GET')
        response = self._request(
            method,
            url,
            data=data,
            client_id=self.client_id,
            client_secret=self.client_secret,
            **kwargs
        )

        exceptions.detect_and_raise_error(response)

        return response

    def authorize_token_url(self, scope=None, redirect_uri=None, **kwargs):
        """
        Step 1: Return the URL the user needs to go to in order to grant us
        authorization to look at their data.  Then redirect the user to that
        URL, open their browser to it, or tell them to copy the URL into their
        browser.

        - redirect_uri: url to which the response will posted. required here
          unless you specify only one Callback URL on the fitbark app or
          you already passed it to the constructor

        for more info see https://dev.fitbark.com/docs/oauth2/
        """

        if redirect_uri:
            self.session.redirect_uri = redirect_uri

        return self.session.authorization_url(self.authorization_url, **kwargs)

    def fetch_access_token(self, code, redirect_uri=None):
        """
        Step 2: Given the code from fitbark from step 1, call
        fitbark again and returns an access token object. Extract the needed
        information from that and save it to use in future API calls.
        the token is internally saved
        """
        if redirect_uri:
            self.session.redirect_uri = redirect_uri
        return self.session.fetch_token(
            self.access_token_url,
            username=self.client_id,
            password=self.client_secret,
            code=code)

    def refresh_token(self):
        """
        Step 3: obtains a new access_token from the the refresh token
        obtained in step 2. Only do the refresh if there is `token_updater(),`
        which saves the token.
        """
        token = {}
        if self.session.token_updater:
            token = self.session.refresh_token(
                self.refresh_token_url,
                auth=HTTPBasicAuth(self.client_id, self.client_secret)
            )
            self.session.token_updater(token)

        return token


class FitBark(object):
    """
    Before using this class, you must request access to the FitBark developer API
    `here <https://www.fitbark.com/dev/>`_. Once approved, you will get the client id
    and secret needed to instantiate this class.
    Before authorizing a user, ensure you update the redirect URIs by following
    the "SETTING OAUTH 2.0 REDIRECT URI'S VIA API" section under their "Authentication" docs.
    See `gather_keys_oauth2.py <https://github.com/alexhouse/python-fitbark/blob/master/gather_keys_oauth2.py>`_
    for a reference implementation of the authorization process. You should
    save ``access_token``, ``refresh_token``, and ``expires_at`` from the
    returned token for each user you authorize.

    When instantiating this class for use with an already authorized user, pass
    in the ``access_token``, ``refresh_token``, and ``expires_at`` keyword
    arguments. We also strongly recommend passing in a ``refresh_cb`` keyword
    argument, which should be a function taking one argument: a token dict.
    When that argument is present, we will automatically refresh the access
    token when needed and call this function so that you can save the updated
    token data. If you don't save the updated information, then you could end
    up with invalid access and refresh tokens, and the only way to recover from
    that is to reauthorize the user.
    """
    API_ENDPOINT = "https://app.fitbark.com/api"
    API_VERSION = 2
    WEEK_DAYS = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    PERIODS = ['1d', '7d', '30d', '1w', '1m', '3m', '6m', '1y', 'max']

    def __init__(self, client_id, client_secret, access_token=None,
                 refresh_token=None, expires_at=None, refresh_cb=None,
                 redirect_uri=None, **kwargs):
        """
        FitBark(<id>, <secret>, access_token=<token>, refresh_token=<token>)
        """
        self.client = FitBarkOauth2Client(
            client_id,
            client_secret,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            refresh_cb=refresh_cb,
            redirect_uri=redirect_uri,
            **kwargs
        )

    def make_request(self, *args, **kwargs):
        # This should handle data level errors, improper requests, and bad
        # serialization
        headers = kwargs.get('headers', {})
        kwargs['headers'] = headers

        response = self.client.make_request(*args, **kwargs)

        if response.status_code == 202:
            return True

        try:
            return json.loads(response.content.decode('utf8'))
        except ValueError:
            raise exceptions.BadResponse

    def user_profile_get(self):
        """
        Get various information about the specified user including name, username (email address), profile picture and Facebook ID.

        :return: user details
        :rtype: json
        """
        url = self._build_api_url('user')
        return self.make_request(url)

    def user_picture_get(self, slug):
        """
        Get the Base64 encoded picture for a specified user.

        :param slug: uuid of the user to look up
        :type slug: uuid
        :return: base64 encoded string of image
        :rtype: json
        """
        url = self._build_api_url('picture/user/{slug}'.format(slug=slug))
        return self.make_request(url)

    def user_related_dogs_get(self):
        """
        Get the dogs related to the logged in user.

        :return: list of dogs
        :rtype: json
        """
        url = self._build_api_url('dog_relations')
        return self.make_request(url)

    def dog_get(self, slug):
        """
        Get various information about a certain dog including name, breed, gender, weight, birthday and picture.

        :param slug: uuid of the dog to look up
        :type slug: uuid
        :return: dog's info
        :rtype: json
        """
        url = self._build_api_url("dog/{slug}".format(slug=slug))
        return self.make_request(url)

    def dog_picture_get(self, slug):
        """
        Get the Base64 encoded picture for a specified dog.

        :param slug: uuid of the dog to return
        :type slug: uuid
        :return: base64 encoded string of image
        :rtype: json
        """
        url = self._build_api_url("picture/dog/{slug}".format(slug=slug))
        return self.make_request(url)

    def dog_related_users_get(self, slug):
        """
        Get a list of users currently associated with a specified dog, together with the type of relationship (Owner or Friend) and privacy settings for each user (how far back in time the activity data is visible).

        :param slug: uuid of the dog to look up
        :type slug: uuid
        :return: list of users
        :rtype: json
        """
        url = self._build_api_url("user_relations/{slug}".format(slug=slug))
        return self.make_request(url)

    def daily_goal_get(self, slug):
        """
        Get a dog’s current daily goal and future daily goals set by an authorized user (if any).

        :param slug: uuid of the dog to look up
        :type slug: uuid
        :return: list of daily goals and dates set
        :rtype: json
        """
        url = self._build_api_url("daily_goal/{slug}".format(slug=slug))
        return self.make_request(url)

    def daily_goal_update(self, slug, data):
        """
        Set the daily goal for a specified dog, and get a response with future daily goals (if any). By default, a future daily goal is repeated for all future dates until another user-set goal is found.
        The daily goal can only be set for future dates, starting from the current date.
        The daily goal value needs to be a positive number.

        :param slug: uuid of the dog to modify
        :type slug: uuid
        :param data: dictionary containing two values, `daily_goal` and `date`
        :type data: dict
        :return: list of all future daily goals
        :rtype: json
        """
        url = self._build_api_url("daily_goal/{slug}".format(slug=slug))
        return self.make_request(url, data)

    def _build_api_url(self, endpoint):
        return "{0}/v{1}/{endpoint}".format(self.API_ENDPOINT, self.API_VERSION, endpoint=endpoint)

    def _get_common_args(self):
        return self.API_ENDPOINT, self.API_VERSION,

    def _get_date_string(self, date):
        if not isinstance(date, str) and date is not None:
            return date.strftime('%Y-%m-%d')
        return date

    def activity_series_get(self, slug, date_from=None, date_to=None, resolution='DAILY'):
        """
        Get historical series data between two specified date times.
        The maximum range is 42 days with daily resolution, and 7 days with hourly resolution.

        :param slug: uuid of the dog to look up
        :type slug: uuid
        :param date_from: the start of the date range to look up
        :type date_from: datetime, date, str
        :param date_to: the end of the date range to look up
        :type date_to: datetime, date, str
        :param resolution: DAILY or HOURLY breakdown
        :type resolution: str
        :return: list of records breaking activity down
        :rtype: json
        """
        today = datetime.date.today()
        date_from = self._get_date_string(date_from)
        date_to = self._get_date_string(date_to)

        if date_from is None:
            date_from = (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        if date_to is None:
            date_to = today.strftime('%Y-%m-%d')

        if resolution not in ['DAILY', 'HOURLY']:
            resolution = 'DAILY'

        if date_to < date_from:
            raise ValueError('The to date must be after the from date')

        data = {
            'activity_series': {
                'slug': slug,
                'from': date_from,
                'to': date_to,
                'resolution': resolution
            }
        }

        url = self._build_api_url("activity_series")
        return self.make_request(url, data, method='POST')

    def dog_similar_stats_get(self, slug):
        """
        Get this dogs, and similar dogs, statistics.

        :param slug: uuid of the dog to look up
        :type slug: uuid
        :return: statistics for dogs similar to the requested dog
        :rtype: json
        """
        url = self._build_api_url("similar_dogs_stats")
        return self.make_request(url, method='POST', data={'slug': slug})

    def activity_totals_get(self, slug, date_from=None, date_to=None):
        """
        Get historical activity data by totaling the historical series between two specified date times.

        :param slug: uuid of the dog to look up
        :type slug: uuid
        :param date_from: the start of the date range to look up
        :type date_from: datetime, date, str
        :param date_to: the end of the date range to look up
        :type date_to: datetime, date, str
        :return: list of records breaking activity down
        :rtype: json
        """
        today = datetime.date.today()
        date_from = self._get_date_string(date_from)
        date_to = self._get_date_string(date_to)

        if date_from is None:
            date_from = (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        if date_to is None:
            date_to = today.strftime('%Y-%m-%d')

        if date_to < date_from:
            raise ValueError('The to date must be after the from date')

        data = {
            'dog': {
                'slug': slug,
                'from': date_from,
                'to': date_to,
            }
        }

        url = self._build_api_url("activity_totals")
        return self.make_request(url, data, method='POST')

    def time_breakdown_get(self, slug, date_from=None, date_to=None):
        """
        Get the time (in minutes) spent at each activity level for a certain dog between two specified date times.

        :param slug: uuid of the dog to look up
        :type slug: uuid
        :param date_from: the start of the date range to look up
        :type date_from: datetime, date, str
        :param date_to: the end of the date range to look up
        :type date_to: datetime, date, str
        :return: total minutes of each activity level (play, active, rest) for the period & dog
        :rtype: json
        """
        today = datetime.date.today()
        date_from = self._get_date_string(date_from)
        date_to = self._get_date_string(date_to)

        if date_from is None:
            date_from = (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        if date_to is None:
            date_to = today.strftime('%Y-%m-%d')

        if date_to < date_from:
            raise ValueError('The to date must be after the from date')

        data = {
            'dog': {
                'slug': slug,
                'from': date_from,
                'to': date_to,
            }
        }

        url = self._build_api_url("time_breakdown")
        return self.make_request(url, data, method='POST')

    def _filter_nones(self, data):
        filter_nones = lambda item: item[1] is not None
        filtered_kwargs = list(filter(filter_nones, data.items()))
        return {} if not filtered_kwargs else dict(filtered_kwargs)
