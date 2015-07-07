import requests
import traceback

from django.conf import settings
from django.core import mail
from django.views.debug import ExceptionReporter, get_exception_reporter_filter
from django.utils.log import AdminEmailHandler


class SlackHandler(AdminEmailHandler):
    def app_setting(self, suffix, default):
        return getattr(settings, 'SLACK_%s' % suffix, default)

    def emit(self, record):
        TOKEN = self.app_setting('TOKEN', None)
        CHANNEL = self.app_setting('CHANNEL', '#general')
        USERNAME = self.app_setting('USERNAME', 'django')
        ICON_URL = self.app_setting('ICON_URL', None)
        ICON_EMOJI = self.app_setting('ICON_EMOJI', None)
        PARAMS = self.app_setting('PARAMS', None)

        try:
            request = record.request
            subject = '%s (%s IP): %s' % (
                record.levelname,
                (
                    'internal' if request.META.get(
                        'REMOTE_ADDR'
                    ) in settings.INTERNAL_IPS
                    else 'EXTERNAL'
                ),
                record.getMessage()
            )
            filter = get_exception_reporter_filter(request)
            request_repr = filter.get_request_repr(request)
        except Exception:
            subject = '%s: %s' % (
                record.levelname,
                record.getMessage()
            )
            request = None
            request_repr = "Request repr() unavailable."
        subject = self.format_subject(subject)

        if record.exc_info:
            exc_info = record.exc_info
            stack_trace = '\n'.join(
                traceback.format_exception(*record.exc_info)
            )
        else:
            exc_info = (None, record.getMessage(), None)
            stack_trace = 'No stack trace available'

        message = "%s\n\n%s" % (stack_trace, request_repr)
        reporter = ExceptionReporter(request, is_email=True, *exc_info)
        html_message = (
            reporter.get_traceback_html() if self.include_html else None
        )

        text = subject+'\n'

        order_list = ['GET', 'POST', 'COOKIES', 'META']

        if PARAMS:
            text += stack_trace + '\n'
            for key in order_list:
                if key in PARAMS and PARAMS[key]:
                    if isinstance(PARAMS[key], dict):
                        text += '%s: {' % key
                        for each in PARAMS[key]:
                            if each in PARAMS[key] and PARAMS[key][each]:
                                if each in eval('request.%s' % key):
                                    text += '%s: %s,\n' % (
                                        each, eval('request.%s["%s"]' % (
                                            key, each)
                                        )
                                    )
                        text += '}\n'
                    else:
                        text += '%s: %s\n' % (key, eval('request.%s' % key))
        else:
            text += message

        data = {
            'token': TOKEN,
            'channel': CHANNEL,
            'icon_url': ICON_URL,
            'icon_emoji': ICON_EMOJI,
            'username': USERNAME,
            'text': '```%s```' % text
        }

        try:
            response = requests.post(
                'https://slack.com/api/chat.postMessage', data=data
            )
            if response.status_code == 200:
                if not response.json()['ok']:
                    mail.mail_admins(
                        subject, message, fail_silently=True,
                        html_message=html_message,
                        connection=self.connection()
                    )
        except:
            mail.mail_admins(
                subject, message, fail_silently=True,
                html_message=html_message,
                connection=self.connection()
            )
