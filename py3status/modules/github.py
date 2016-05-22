# -*- coding: utf-8 -*-
"""
Display Github notifications and issue/pull requests for a repo.

To check notifications a Github `username` and `personal access token` are
required.  You can create a personal access token at
https://github.com/settings/tokens The only `scope` needed is `notifications`,
which provides readonly access to notifications.

The Github API is rate limited so setting `cache_timeout` too small may cause
issues see https://developer.github.com/v3/#rate-limiting for details


Configuration parameters:
    auth_token: Github personal access token, needed to check notifications
        see above.
        (default None)
    button_notifications: Button that when clicked opens the notification page
        on github.com. Setting to `0` disables.
        (default 1)
    cache_timeout: How often we refresh this module in seconds
        (default 60)
    format: Format of output
        (default '{repo} {issues}/{pull_requests}{notifications}')
    format_notifications: Format of `{notification}` status placeholder.
        (default ' 🔔{count}')
    notifications: Type of notifications can be `all` for all notifications or
        `repo` to only get notifications for the repo specified.  If repo is
        not provided then all notifications will be checked.
        (default 'all')
    repo: Github repo to check
        (default 'ultrabug/py3status')
    username: Github username, needed to check notifications.
        (default None)

Format of status string placeholders:
    {repo} the name of the repository being checked.
    {issues} Number of open issues.
    {pull_requests} Number of open pull requests
    {notifications} Notifications.  If no notifications this will be empty.
    {count} __Only__ used in `format_notifications`,
        the number of unread notifications

Requires:
    requests: python module from pypi https://pypi.python.org/pypi/requests

Examples:

```
# set github access credentials
github {
    auth_token = '40_char_hex_access_token'
    username = 'my_username'
}

# just check for any notifications
github {
    auth_token = '40_char_hex_access_token'
    username = 'my_username'
    format = 'Github{notifications}'
    format_notifications = ' {count}'
}
```

@author tobes
"""
from shlex import split
from subprocess import call

import requests


GITHUB_API_URL = 'https://api.github.com'
GITHUB_NOTIFICATION_URL = 'https://github.com/notifications'


class Py3status:
    auth_token = None
    button_notifications = 1
    cache_timeout = 60
    format = '{repo} {issues}/{pull_requests}{notifications}'
    format_notifications = u' 🔔{count}'
    notifications = 'all'
    repo = 'ultrabug/py3status'
    username = None

    def __init__(self):
        self.first = True
        self.notification_warning = False
        self.repo_warning = False
        self._issues = '?'
        self._pulls = '?'

    def _github_count(self, url):
        '''
        Get counts for requests that return 'total_count' in the json response.
        '''
        if self.first:
            return '?'
        url = GITHUB_API_URL + url + '&per_page=1'
        # if we have authentication details use them as we get better
        # rate-limiting.
        if self.username and self.auth_token:
            auth = (self.username, self.auth_token)
        else:
            auth = None
        try:
            info = requests.get(url, 'GET', timeout=10, auth=auth)
        except requests.ConnectionError:
            return
        if info and info.status_code == 200:
            return(int(info.json()['total_count']))
        if info.status_code == 422:
            if not self.repo_warning:
                self.py3.notify_user('Github repo cannot be found.')
                self.repo_warning = True
        return '?'

    def _notifications(self):
        '''
        Get the number of unread notifications.
        '''
        if not self.username or not self.auth_token:
            if not self.notification_warning:
                self.py3.notify_user('Github module needs username and '
                                     'auth_token to check notifications.')
                self.notification_warning = True
            return '?'
        if self.first:
            return '?'
        if self.notifications == 'all' or not self.repo:
            url = GITHUB_API_URL + '/notifications'
        else:
            url = GITHUB_API_URL + '/repos/' + self.repo + '/notifications'
        url += '?per_page=100'
        try:
            info = requests.get(url, timeout=10,
                                auth=(self.username, self.auth_token))
        except requests.ConnectionError:
            return
        if info.status_code == 200:
            return len(info.json())
        if info.status_code == 404:
            if not self.repo_warning:
                self.py3.notify_user('Github repo cannot be found.')
                self.repo_warning = True

    def github(self):
        status = {}
        urgent = False
        # issues
        if self.repo and '{issues}' in self.format:
            url = '/search/issues?q=state:open+type:issue+repo:' + self.repo
            self._issues = self._github_count(url) or self._issues
        status['issues'] = self._issues
        # pull requests
        if self.repo and '{pull_requests}' in self.format:
            url = '/search/issues?q=state:open+type:pr+repo:' + self.repo
            self._pulls = self._github_count(url) or self._pulls
        status['pull_requests'] = self._pulls
        # notifications
        if '{notifications}' in self.format:
            self._notify = self._notifications() or self._notify
            notifications = self._notify
            if notifications and notifications != '?':
                notify = self.format_notifications.format(count=notifications)
                urgent = True
            else:
                notify = ''
            status['notifications'] = notify
        else:
            notifications = None
        # repo
        status['repo'] = self.repo

        if self.first:
            cached_until = 0
            self.first = False
        else:
            cached_until = self.py3.time_in(self.cache_timeout)

        return {
            'full_text': self.py3.safe_format(self.format, status),
            'cached_until': cached_until,
            'urgent': urgent
        }

    def on_click(self, event):
        button = event['button']
        if self.button_notifications and self.button_notifications == button:
            # open github notifications page in default browser
            cmd = 'xdg-open {}'.format(GITHUB_NOTIFICATION_URL)
            call(split(cmd))
