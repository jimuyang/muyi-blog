import asyncio
from models import User
import orm_core

async def test(loop):
    await orm_core.create_pool(loop=loop, user='www-data', password='www-data', database='py_nature_web')
    user = User(name='testUser', email='test@example.com', password='1345345', image='about:blank')
    await user.save()

lp = asyncio.get_event_loop()
lp.run_until_complete(test(lp))
lp.close()

# test(None)

