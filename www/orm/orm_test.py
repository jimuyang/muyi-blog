import asyncio
from models import User
import cororm

async def test(loop):
    await cororm.create_pool(loop=loop, user='www-data', password='www-data', database='py_nature_web')
    user = User(name='testUser', email='test@example.com', password='1345345', image='about:blank')
    await user.save()

lp = asyncio.get_event_loop()
lp.run_until_complete(test(lp))
lp.run_forever()

# test(None)

