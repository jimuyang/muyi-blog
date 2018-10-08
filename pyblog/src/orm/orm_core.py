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

def create_args_string(num):
    '''
    生成类似 ?, ?, ? 的东西
    '''
    L = []
    for _ in range(num):
        L.append('?')
    return ', '.join(L)



class ModelMeta(type):
    '''
    model meta
    '''

    def __new__(cls, name, bases, attrs):
        # Model class
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        table_name = attrs.get('__table__', None) or name
        logging.info('model found: %s (table: %s)', name, table_name)
        mappings = dict()  # 字段和属性映射
        fields = []  # 表字段 不包括主键
        primary_key = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('  mapping found: %s ==> %s', k, v)
                mappings[k] = v
                if v.primary_key:
                    # 找到主键
                    if primary_key:
                        raise ValueError(
                            'Duplicate primary key for field: %s' % k)
                    primary_key = k
                else:
                    fields.append(k)
        if not primary_key:
            raise ValueError('Primary key not found.')
        # 从attrs里删除
        for k in mappings.keys():
            attrs.pop(k)

        fields_str = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings
        attrs['__table__'] = table_name
        attrs['__primary_key__'] = primary_key
        attrs['__fields__'] = fields
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primary_key, ', '.join(fields_str), table_name)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values ( %s )' % (table_name,', '.join(fields_str), primary_key, create_args_string(len(fields_str)+1))
        attrs['__update__'] = 'update `%s` set %s where `%s` = ?' % (table_name, ', '.join(map(lambda f: '`%s` = ?' % (mappings.get(f).name or f), fields)), primary_key)
        attrs['__delete__'] = 'delete from `%s` where `%s` = ?' % (table_name, primary_key)
        return type.__new__(cls, name, bases, attrs)

class Model(dict, metaclass=ModelMeta):
    
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)
    
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(
                r"'Model' object has no attribute '%s'" % key)
    
    def __setattr__(self, key, value):
        self[key] = value

    def get_value(self, key):
        return getattr(self, key, None)
    
    def get_value_or_default(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s : %s', key, str(value))
                setattr(self, key, value)
        return value
    
    @classmethod
    async def find_all(cls, where=None, args=None, **kw):
        '''
        find objects by where condition
        '''
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderby = kw.get('orderBy', None)
        if orderby:
            sql.append('order by')
            sql.append(orderby)

        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]
            
    @classmethod
    async def count(cls, selectField, where=None, args=None):
        '''
        find number by select and where.
        '''
        sql = ['select %s, _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']
    
    @classmethod
    async def find(cls, pk):
        '''
        find object by primary key
        '''
        rs = await select('%s where `%s` = ?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.get_value_or_default, self.__fields__))
        args.append(self.get_value_or_default(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warning('failed to insert record: affected rows: %s', rows)
    
    async def update(self):
        args = list(map(self.get_value, self.__fields__))
        args.append(self.get_value(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warning('failed to update by primary key: affected rows: %s', rows)
    
    async def delete(self):
        args = [self.get_value(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warning('failed to remove by primary key: affected rows: %s', rows)


def main():
    Model(hello='world')


if __name__ == '__main__':
    main()
