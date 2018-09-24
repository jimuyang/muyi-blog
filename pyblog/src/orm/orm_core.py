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


async def create_pool(loop, **kw):
    '''
    创建一个aiomysql连接池
    '''
    logging.info('create database connection pool...')
    global __mysql_connection_pool
    __mysql_connection_pool = await aiomysql.create_pool(
        loop=loop,
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['database'],
        charset=kw.get('charset', 'utf-8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
    )


async def select(sql, args, size=None):
    '''
    执行一个select sql
    '''
    log_sql(sql, args=args)
    # global __mysql_connection_pool
    async with __mysql_connection_pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql.replace('?', '%s'), args or ())
            if size:
                rs = await cursor.fetchmany(size)
            else:
                rs = await cursor.fetchall()
    logging.info('rows returned: %s', len(rs))
    return rs


async def execute(sql, args, autocommit=True):
    '''
    执行一个update/delete sql
    '''
    log_sql(sql, args=args)
    # global __mysql_connection_pool
    async with __mysql_connection_pool.get() as conn:
        if not autocommit:
            await conn.begin()
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(sql.replace('?', '%s'), args or ())
                affected = cursor.rowcount
            if not autocommit:
                await conn.commit()
        except BaseException as be:
            if not autocommit:
                await conn.rollback()
            raise be
    return affected


def _create_args_string(num):
    '''
    生成类似 ?, ?, ?的string
    '''
    li = []
    for _ in range(num):
        li.append('?')
    return ', '.join(li)


class Field(object):
    '''
    field 用来进行属性和列之间的映射
    '''
    def __init__(self, name, column_type, default, primary_key=False):
        self.name = name                # 列名
        self.column_type = column_type  # 列的类型
        self.primary_key = primary_key  # 是否为主键
        self.default = default          # 默认值

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):

    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):

    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)


class IntegerField(Field):

    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)


class FloatField(Field):

    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)


class TextField(Field):

    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)


class ModelMeta(type):
    '''
    model meta
    '''

    def __new__(cls, *args, **kw):
        return type.__new__(cls, args, kw)

class Model(dict, metaclass=ModelMeta):
    '''
    model
    '''

    def __init__(self, **kw):
        super(Model, self).__init__(kw)


def main():
    Model(hello='world')

if __name__ == '__main__':
    main()