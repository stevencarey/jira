# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import threading
import json
import pytz
import re
from datetime import datetime
from collections import namedtuple

from .resilientsession import raise_on_error

IssueHistory = namedtuple('IssueHistory', [
    'id',
    'fda',
    'dt_issue_created',
    'creator_timezone',
    'author',
    'author_email',
    'author_display_name',
    'user_active',
    'change_created',
    'field',
    'from_project',
    'to_project',
    'from_squad',
    'to_squad',
    'from_assignee',
    'to_assignee',
    'from_status',
    'to_status',
    'timezone'
])



class CaseInsensitiveDict(dict):

    """
    A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``collections.MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.

    """

    def __init__(self, *args, **kw):
        super(CaseInsensitiveDict, self).__init__(*args, **kw)

        self.itemlist = {}
        for key, value in super(CaseInsensitiveDict, self).items():
            if key != key.lower():
                self[key.lower()] = value
                self.pop(key, None)

        #self.itemlist[key.lower()] = value

    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(key.lower(), value)

    # def __iter__(self):
    #    return iter(self.itemlist)

    # def keys(self):
    #    return self.itemlist

    # def values(self):
    #    return [self[key] for key in self]

    # def itervalues(self):
    #    return (self[key] for key in self)


def threaded_requests(requests):
    for fn, url, request_args in requests:
        th = threading.Thread(
            target=fn, args=(url,), kwargs=request_args, name=url,
        )
        th.start()

    for th in threading.enumerate():
        if th.name.startswith('http'):
            th.join()


def json_loads(r):
    raise_on_error(r)
    if len(r.text):  # r.status_code != 204:
        return json.loads(r.text)
    else:
        # json.loads() fails with empy bodies
        return {}


def make_naive_datetime(date_string):
    try:
        # convert datetime to string.
        dt = datetime.strftime(date_string, "%Y-%m-%dT%H:%M")

        # stip everything after seconds. ie all +HH:MM for timezone.
        dt = re.sub(r':\d{2}\..*$', '', dt)

    except TypeError:
        dt = re.sub(r':\d{2}\..*$', '', date_string)

    return datetime.strptime(dt, "%Y-%m-%dT%H:%M")


def get_utc(date_string, timezone='Europe/London'):
    '''
    :type date_string str
    :rtype datetime
    '''
    naive = make_naive_datetime(date_string)
    local = pytz.timezone(timezone)
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt
