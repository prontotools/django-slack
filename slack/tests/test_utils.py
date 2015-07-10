import logging
from mock import patch

from django.core import mail
from django.http import request, QueryDict
from django.test import SimpleTestCase
from django.test.utils import override_settings
from admin_scripts.tests import AdminScriptTestCase


class SlackHandlerTest(SimpleTestCase, AdminScriptTestCase):
    def setUp(self):
        self.logger = logging.getLogger('django.request')

        self.req = request.HttpRequest()
        self.req.GET = QueryDict('test_get=1')
        self.req.POST = QueryDict('test_post=1')
        self.req.META['SERVER_NAME'] = 'server_name'
        self.req.COOKIES['sessionid'] = '2441'
        log_config = """{
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'slack': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'slack.utils.SlackHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'slack'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}"""
        self.write_settings('settings.py', sdict={'LOGGING': log_config})

    def get_slack_handler(self, logger):
        slack_handler = [
            h for h in logger.handlers
            if h.__class__.__name__ == "SlackHandler"
        ][0]
        return slack_handler

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS={
            'GET': True,
            'POST': True,
            'COOKIES': {
                'sessionid': True
            },
            'META': {
                'SERVER_NAME': True
            }
        }
    )
    @patch('slack.utils.requests.post')
    def test_should_send_message_to_slack_with_correct_parameter(
        self, mock_request
    ):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'ok': True}

        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            slack_handler.filters = []

            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n"
            text += "GET: <QueryDict: {u'test_get': [u'1']}>\n"
            text += "POST: <QueryDict: {u'test_post': [u'1']}>\n"
            text += "COOKIES: {sessionid: 2441,\n}"
            text += "\nMETA: {SERVER_NAME: server_name,\n}\n```"
            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 1)
        finally:
            slack_handler.filters = orig_filters

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS=None
    )
    @patch('slack.utils.requests.post')
    def test_should_send_all_parameter_when_not_set_slack_param(
        self, mock_request
    ):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'ok': True}

        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            slack_handler.filters = []

            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n\n"
            text += "<HttpRequest\npath:,\n"
            text += "GET:<QueryDict: {u'test_get': [u'1']}>,\n"
            text += "POST:<QueryDict: {u'test_post': [u'1']}>,\n"
            text += "COOKIES:{'sessionid': '2441'},\n"
            text += "META:{'SERVER_NAME': 'server_name'}>```"

            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 1)
        finally:
            slack_handler.filters = orig_filters

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS={
            'POST': True,
            'COOKIES': {
                'sessionid': True
            },
            'META': {
                'SERVER_NAME': True
            }
        }
    )
    @patch('slack.utils.requests.post')
    def test_not_set_get_should_not_send_get_query_string_data_to_slack(
        self, mock_request
    ):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'ok': True}

        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n"
            text += "POST: <QueryDict: {u'test_post': [u'1']}>\n"
            text += "COOKIES: {sessionid: 2441,\n}"
            text += "\nMETA: {SERVER_NAME: server_name,\n}\n```"
            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 1)
        finally:
            slack_handler.filters = orig_filters

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS={
            'GET': True,
            'COOKIES': {
                'sessionid': True
            },
            'META': {
                'SERVER_NAME': True
            }
        }
    )
    @patch('slack.utils.requests.post')
    def test_not_post_should_not_send_post_query_string_data_to_slack(
        self, mock_request
    ):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'ok': True}

        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n"
            text += "GET: <QueryDict: {u'test_get': [u'1']}>\n"
            text += "COOKIES: {sessionid: 2441,\n}\n"
            text += "META: {SERVER_NAME: server_name,\n}\n```"

            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 1)
        finally:
            slack_handler.filters = orig_filters

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS={
            'GET': True,
            'POST': True,
            'COOKIES': {
                'sessionid': True
            },
        }
    )
    @patch('slack.utils.requests.post')
    def test_not_set_meta_should_not_send_meta_data_to_slack(
        self, mock_request
    ):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'ok': True}

        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n"
            text += "GET: <QueryDict: {u'test_get': [u'1']}>\n"
            text += "POST: <QueryDict: {u'test_post': [u'1']}>\n"
            text += "COOKIES: {sessionid: 2441,\n}\n```"
            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 1)
        finally:
            slack_handler.filters = orig_filters

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS={
            'GET': True,
            'POST': True,
            'META': {
                'SERVER_NAME': True
            }
        }
    )
    @patch('slack.utils.requests.post')
    def test_not_set_cookie_should_not_send_cookie_data_to_slack(
        self, mock_request
    ):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'ok': True}

        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n"
            text += "GET: <QueryDict: {u'test_get': [u'1']}>\n"
            text += "POST: <QueryDict: {u'test_post': [u'1']}>\n"
            text += "META: {SERVER_NAME: server_name,\n}\n```"

            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 1)
        finally:
            slack_handler.filters = orig_filters

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS={
            'GET': False,
            'POST': True,
            'COOKIES': {
                'sessionid': True
            },
            'META': {
                'SERVER_NAME': True
            }
        }
    )
    @patch('slack.utils.requests.post')
    def test_set_get_false_should_not_send_get_query_string_data_to_slack(
        self, mock_request
    ):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'ok': True}

        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n"
            text += "POST: <QueryDict: {u'test_post': [u'1']}>\n"
            text += "COOKIES: {sessionid: 2441,\n}"
            text += "\nMETA: {SERVER_NAME: server_name,\n}\n```"
            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 1)
        finally:
            slack_handler.filters = orig_filters

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS={
            'GET': True,
            'POST': True,
            'COOKIES': {
                'sessionid': True
            },
            'META': False
        }
    )
    @patch('slack.utils.requests.post')
    def test_set_meta_false_should_not_send_meta_data_to_slack(
        self, mock_request
    ):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'ok': True}

        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n"
            text += "GET: <QueryDict: {u'test_get': [u'1']}>\n"
            text += "POST: <QueryDict: {u'test_post': [u'1']}>\n"
            text += "COOKIES: {sessionid: 2441,\n}\n```"
            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 1)
        finally:
            slack_handler.filters = orig_filters

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS={
            'GET': True,
            'POST': True,
            'COOKIES': {
                'sessionid': True
            },
            'META': {}
        }
    )
    @patch('slack.utils.requests.post')
    def test_set_meta_with_empty_list_should_not_send_meta_data_to_slack(
        self, mock_request
    ):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'ok': True}

        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n"
            text += "GET: <QueryDict: {u'test_get': [u'1']}>\n"
            text += "POST: <QueryDict: {u'test_post': [u'1']}>\n"
            text += "COOKIES: {sessionid: 2441,\n}\n```"
            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 1)
        finally:
            slack_handler.filters = orig_filters

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS={
            'GET': True,
            'POST': True,
            'COOKIES': {
                'sessionid': True
            },
            'META': {}
        }
    )
    @patch('slack.utils.requests.post')
    def test_status_from_slack_false_should_send_email(
        self, mock_request
    ):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'ok': False}

        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n"
            text += "GET: <QueryDict: {u'test_get': [u'1']}>\n"
            text += "POST: <QueryDict: {u'test_post': [u'1']}>\n"
            text += "COOKIES: {sessionid: 2441,\n}\n```"
            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 2)
        finally:
            slack_handler.filters = orig_filters

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS={
            'GET': True,
            'POST': True,
            'COOKIES': {
                'sessionid': True
            },
            'META': {}
        }
    )
    @patch('slack.utils.requests.post')
    def test_send_to_slack_error_should_send_email(
        self, mock_request
    ):
        mock_request.side_effect = Exception()
        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n"
            text += "GET: <QueryDict: {u'test_get': [u'1']}>\n"
            text += "POST: <QueryDict: {u'test_post': [u'1']}>\n"
            text += "COOKIES: {sessionid: 2441,\n}\n```"
            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 2)
        finally:
            slack_handler.filters = orig_filters

    @override_settings(
        SLACK_TOKEN='fsk33',
        SLACK_CHANNEL='#pw-errors',
        SLACK_PARAMS={
            'GET': True,
            'POST': True,
            'COOKIES': {
                'sessionid': True
            },
            'META': {'SERVER_NAME': True}
        }
    )
    @patch('slack.utils.requests.post')
    def test_should_not_error_when_no_meta_data_in_request(
        self, mock_request
    ):
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'ok': True}

        del(self.req.META['SERVER_NAME'])

        slack_handler = self.get_slack_handler(self.logger)

        orig_filters = slack_handler.filters
        try:
            self.logger.error(
                "Test 500",
                extra={
                    'status_code': 500,
                    'request': self.req,
                }
            )

            text = "```ERROR (EXTERNAL IP): Test 500\n"
            text += "No stack trace available\n"
            text += "GET: <QueryDict: {u'test_get': [u'1']}>\n"
            text += "POST: <QueryDict: {u'test_post': [u'1']}>\n"
            text += "COOKIES: {sessionid: 2441,\n}\n"
            text += "META: {}\n```"
            mock_request.assert_called_once_with(
                'https://slack.com/api/chat.postMessage',
                data={
                    'username': 'django',
                    'icon_url': None,
                    'token': 'fsk33',
                    'icon_emoji': None,
                    'text': text,
                    'channel': '#pw-errors'
                }
            )

            self.assertEqual(len(mail.outbox), 1)
        finally:
            slack_handler.filters = orig_filters
