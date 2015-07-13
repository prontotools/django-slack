# Django Slack
[![Build
Status](https://travis-ci.org/prontodev/django-slack.svg?branch=master)](https://travis-ci.org/prontodev/django-slack)

## Installation

```
pip install git+git://github.com/prontodev/django-slack.git
```

## Django Settings Example

```
LOGGING = {
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
}
```

```
IS_SLACK_ENABLED = True
SLACK_TOKEN = '<token>'
SLACK_CHANNEL = '#<channel>'
SLACK_USERNAME = '<username>'

SLACK_PARAMS = {
    'GET': True,
    'POST': True,
    'META': {
        'SERVER_NAME': True,
        'HTTP_ACCEPT': True
    }
}
```
