import orm, asyncio
from models import User, BLog, Comment

async def test(loop):
    await orm.create_pool(loop=loop, user='www-data', password='www-data', database='py_nature_web')
    user = User(name='testUser', email='test@example.com', password='1345345', image='about:blank')
    await user.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.run_forever()

# test(None)

