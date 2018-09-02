#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Jimu Yang'

'''
url handles.
'''

from webcore.coroweb import get, post
from orm.models import User

@get('/')
async def index(request):
    users = await User.findAll()
    return {
        '__template__': 'show_all_users.html',
        'users': users
    }

