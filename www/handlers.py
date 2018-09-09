#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Jimu Yang'

'''
url handles.
'''

from webcore.coroweb import get, post
from orm.models import User, BLog
import time

@get('/')
async def index(request):
    users = await User.findAll()
    return {
        '__template__': 'show_all_users.html',
        'users': users
    }


@get('/blogs')
async def blogs(request):
    summary = 'Lorem ipsum dolor sit amet, consectufsfm,sf sf sfsaffsf  wfweg f3fqw'
    blogs = [
        BLog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        BLog(id='2', name='Something new', summary=summary, created_at=time.time()-3600),
        BLog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200),
    ]
    return { 
        '__template__': 'blogs.html',
        'blogs': blogs
    }
    