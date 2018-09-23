#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Jimu Yang'

'''
简单的Python ORM框架
'''

import logging
import aiomysql


# 打印sql
def log_sql(sql, args=()):
    logging.info('SQL: %s', sql)

# global 定义的变量，表明其作用域在局部以外，即局部函数执行完之后，不销毁 函数内部以global定义的变量

'''
创建一个aiomysql连接池
'''
async def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __mysql_connection_pool
    __mysql_connection_pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['database'],
        charset=kw.get('charset', 'utf-8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

