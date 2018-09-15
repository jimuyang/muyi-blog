#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Jimu Yang'

'''
url handles.
'''

from webcore.coroweb import get, post
from webcore.api_error import APIError, APIValueError
from orm.models import User, BLog
from conf.configs import configs
import time, hashlib

COOKIE_NAME = 'user_session'
_COOKIE_KEY = configs.session.secret
# print(_COOKIE_KEY)

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


@get('/api/users')
async def api_get_users():
    users = await User.findAll(orderBy='created_at desc')
    for user in users:
        user.password = '****'
    return dict(users=users)

@post('/api/user-auth')
async def user_auth(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email')
    if not passwd:
        raise APIValueError('passwd', 'Invalid passwd')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # check password:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    # user auth ok, set cookie:
    resp = web.Response()    
    resp.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '****'
    resp.content_type = 'application/json'
    resp.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return resp
    
    
    

def user2cookie(user, max_age):
    '''
    Generate cookie string by user.
    '''
    # build cookie string by: id-expires-sha1
    expire_at = str(int(time.time() + max_age)
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expire_at, _COOKIE_KEY)
    list = [user.id, expire_at, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(list)


async def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        list = cookie_str.split('-')
        if len(list) != 3:
            return None
        user_id, expire_at, sha1 = list
        if int(expire_at) < time.time():
            return None
        user = await User.find(user_id)
        if user is None:
            return None
        str = '%s-%s-%s-%s' % (user_id, user.passwd, expire_at, _COOKIE_KEY)
        if sha1 != hashlib.sha1(str.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '****'
        return user
    except Exception as e:
        logging.exception(e)
        return None
    