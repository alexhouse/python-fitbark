from unittest import TestCase

import datetime
import mock
import requests

from fitbark import FitBark
from fitbark.exceptions import Timeout

URLBASE = "%s/v%s/" % (FitBark.API_ENDPOINT, FitBark.API_VERSION)


class TestBase(TestCase):
    def setUp(self):
        self.fb = FitBark('x', 'y')

    def common_api_test(self, funcname, args, kwargs, expected_args, expected_kwargs):
        # Create a fitbark object, call the named function on it with the given
        # arguments and verify that make_request is called with the expected args and kwargs
        with mock.patch.object(self.fb, 'make_request') as make_request:
            retval = getattr(self.fb, funcname)(*args, **kwargs)
        mr_args, mr_kwargs = make_request.call_args
        self.assertEqual(expected_args, mr_args)
        self.assertEqual(expected_kwargs, mr_kwargs)

    def verify_raises(self, funcname, args, kwargs, exc):
        self.assertRaises(exc, getattr(self.fb, funcname), *args, **kwargs)


class TimeoutTest(TestCase):

    def setUp(self):
        self.fb = FitBark('x', 'y')
        self.fb_timeout = FitBark('x', 'y', timeout=10)

        self.test_url = 'invalid://do.not.connect'

    def test_fb_without_timeout(self):
        with mock.patch.object(self.fb.client.session, 'request') as request:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.content = b'{}'
            request.return_value = mock_response
            result = self.fb.make_request(self.test_url)

        request.assert_called_once()
        self.assertNotIn('timeout', request.call_args[1])
        self.assertEqual({}, result)

    def test_fb_with_timeout__timing_out(self):
        with mock.patch.object(self.fb_timeout.client.session, 'request') as request:
            request.side_effect = requests.Timeout('Timed out')
            with self.assertRaisesRegex(Timeout, 'Timed out'):
                self.fb_timeout.make_request(self.test_url)

        request.assert_called_once()
        self.assertEqual(10, request.call_args[1]['timeout'])

    def test_fb_with_timeout__not_timing_out(self):
        with mock.patch.object(self.fb_timeout.client.session, 'request') as request:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.content = b'{}'
            request.return_value = mock_response

            result = self.fb_timeout.make_request(self.test_url)

        request.assert_called_once()
        self.assertEqual(10, request.call_args[1]['timeout'])
        self.assertEqual({}, result)


class APITest(TestBase):
    """
    Tests for python-fitbark API, not directly involved in getting
    authenticated
    """

    def test_make_request(self):
        # If make_request returns a response with status 200,
        # we get back the json decoded value that was in the response.content
        ARGS = (1, 2)
        KWARGS = {'a': 3, 'b': 4, 'headers': {}}
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.content = b"1"
        with mock.patch.object(self.fb.client, 'make_request') as client_make_request:
            client_make_request.return_value = mock_response
            retval = self.fb.make_request(*ARGS, **KWARGS)
        self.assertEqual(1, client_make_request.call_count)
        self.assertEqual(1, retval)
        args, kwargs = client_make_request.call_args
        self.assertEqual(ARGS, args)
        self.assertEqual(KWARGS, kwargs)

    def test_make_request_202(self):
        # If make_request returns a response with status 202,
        # we get back True
        mock_response = mock.Mock()
        mock_response.status_code = 202
        mock_response.content = "1"
        ARGS = (1, 2)
        KWARGS = {'a': 3, 'b': 4}
        with mock.patch.object(self.fb.client, 'make_request') as client_make_request:
            client_make_request.return_value = mock_response
            retval = self.fb.make_request(*ARGS, **KWARGS)
        self.assertEqual(True, retval)


class ResourceAccessTest(TestBase):
    """
    Class for testing the FitBark Resource Access API:
    https://dev.fitbark.com/docs/
    """

    def test_user_profile_get(self):
        """
        Test getting a user profile.
        https://www.fitbark.com/dev/

        Tests the following HTTP method/URLs:
        GET https://app.fitbark.com/api/v2/user
        """
        self.common_api_test('user_profile_get', (), {}, (URLBASE + "user",), dict())

    def test_user_picture_get(self):
        user_slug = 'user-uuid'
        self.common_api_test('user_picture_get', (), dict(slug=user_slug), (URLBASE + "picture/user/%s" % user_slug,),
                             {})

    def test_user_related_dogs_get(self):
        self.common_api_test('user_related_dogs_get', (), {}, (URLBASE + 'dog_relations',), {})

    def test_dog_get(self):
        dog_slug = 'dog-uuid'
        self.common_api_test('dog_get', (), dict(slug=dog_slug), (URLBASE + 'dog/%s' % dog_slug,), {})

    def test_dog_picture_get(self):
        dog_slug = 'dog-uuid'
        self.common_api_test('dog_picture_get', (), dict(slug=dog_slug), (URLBASE + 'picture/dog/%s' % dog_slug,), {})

    def test_dog_related_users_get(self):
        dog_slug = 'dog-uuid'
        self.common_api_test('dog_related_users_get', (), dict(slug=dog_slug),
                             (URLBASE + 'user_relations/%s' % dog_slug,), {})

    def test_daily_goal_get(self):
        dog_slug = 'dog-uuid'
        self.common_api_test('daily_goal_get', (), dict(slug=dog_slug), (URLBASE + 'daily_goal/%s' % dog_slug,), {})

    def test_daily_goal_update(self):
        dog_slug = 'dog-uuid'
        self.common_api_test(
            'daily_goal_update', (dog_slug, {}), {},
            (URLBASE + 'daily_goal/%s' % dog_slug, {}), {})
        self.common_api_test(
            'daily_goal_update', (dog_slug, {'daily_goal': 7000}), {},
            (URLBASE + 'daily_goal/%s' % dog_slug, {'daily_goal': 7000}), {})

    def test_activity_series_get(self):
        dog_slug = 'dog-uuid'
        date = datetime.date.today()
        yesterday = (date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        tomorrow = (date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        today = date.strftime('%Y-%m-%d')

        built_data = {
            'activity_series': {
                'slug': dog_slug,
                'from': yesterday,
                'resolution': 'DAILY',
                'to': today
            }
        }

        self.common_api_test('activity_series_get', (),
                             dict(slug=dog_slug, date_from=yesterday, date_to=today, resolution='DAILY'),
                             (URLBASE + 'activity_series', built_data,), {'method': 'POST'})

        self.common_api_test('activity_series_get', (),
                             dict(slug=dog_slug, date_from=yesterday, date_to=today, resolution='RANDOM'),
                             (URLBASE + 'activity_series', built_data,), {'method': 'POST'})

        self.common_api_test('activity_series_get', (),
                             dict(slug=dog_slug, ),
                             (URLBASE + 'activity_series', built_data,), {'method': 'POST'})

        built_data = {
            'activity_series': {
                'slug': dog_slug,
                'from': '2019-01-01',
                'resolution': 'DAILY',
                'to': today
            }
        }
        self.common_api_test('activity_series_get', (), dict(slug=dog_slug, date_from='2019-01-01'),
                             (URLBASE + 'activity_series', built_data,), {'method': 'POST'})

        self.verify_raises('activity_series_get', (), dict(slug=dog_slug, date_from=tomorrow), ValueError)

    def test_dog_similar_stats_get(self):
        dog_slug = 'dog-uuid'
        self.common_api_test('dog_similar_stats_get', (dog_slug,), {}, (URLBASE + 'similar_dogs_stats',),
                             {'data': {'slug': dog_slug}, 'method': 'POST'})

    def test_activity_totals_get(self):
        # no data requests from yesterday to today
        today = datetime.date.today()
        dog_slug = 'dog-uuid'

        self.common_api_test('activity_totals_get', (), dict(slug=dog_slug), (URLBASE + 'activity_totals',
                                                                              {'dog': {
                                                                                  'slug': dog_slug,
                                                                                  'from': (today - datetime.timedelta(
                                                                                      days=1)).strftime('%Y-%m-%d'),
                                                                                  'to': today.strftime('%Y-%m-%d')
                                                                              }}), {'method': 'POST'})

        # provided dates are used
        self.common_api_test('activity_totals_get', (),
                             dict(slug=dog_slug, date_from='2019-01-01', date_to='2019-01-31'),
                             (URLBASE + 'activity_totals',
                              {'dog': {
                                  'slug': dog_slug,
                                  'from': '2019-01-01',
                                  'to': '2019-01-31'
                              }},), {'method': 'POST'})

        # to date defaults to today
        self.common_api_test('activity_totals_get', (), dict(slug=dog_slug, date_from='2019-02-01'),
                             (URLBASE + 'activity_totals',
                              {'dog': {
                                  'slug': dog_slug,
                                  'from': '2019-02-01',
                                  'to': today.strftime('%Y-%m-%d')
                              }},), {'method': 'POST'})

        # validate to is after from
        self.verify_raises('activity_totals_get', (), dict(slug=dog_slug, date_from='2019-01-15', date_to='2019-01-01'),
                           ValueError)

    def test_time_breakdown_get(self):
        slug = 'dog-uuid'
        today = datetime.date.today()
        yesterday = (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        tomorrow = (today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        today = today.strftime('%Y-%m-%d')

        self.common_api_test('time_breakdown_get', (), dict(slug=slug),
                             (URLBASE + 'time_breakdown', {'dog': {'slug': slug, 'from': yesterday, 'to': today}},),
                             {'method': 'POST'})
        self.verify_raises('time_breakdown_get', (), dict(slug=slug, date_from=tomorrow), ValueError)
