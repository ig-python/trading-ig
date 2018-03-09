import logging
from pyIG.rest import IGParams, IGClient, Order, OrderType, Side, Money
import os
import asyncio

logger = logging.getLogger()
logger.setLevel(logging.INFO)

params = IGParams()
params.Url = os.environ['IG_URL']
params.Key = os.environ['X_IG_API_KEY']
params.Identifier = os.environ['IDENTIFIER']
params.Password = os.environ['PASSWORD']


async def main():
    async with IGClient(params, logger) as client:
        auth = await client.Login()
        print(auth)

        order = Order('IX.D.SPTRD.DAILY.IP', Side.Buy, Money(100, 'GBP'), OrderType.Market, 'DFB')

        deal = await client.CreatePosition(order)
        print(deal)
        
        activities = await client.GetActivities('2018-02-05', True)
        print(activities)
        if 'activities' in activities:
            stopTriggered = [tran for tran in activities['activities']
                             if tran['channel'] == 'SYSTEM' and 'details' in tran
                             for action in tran['details']['actions'] if action['actionType'] == 'POSITION_CLOSED']

            for stop in stopTriggered:
                print(stop)

        await client.Logout()

if __name__ == '__main__':
    app_loop = asyncio.get_event_loop()
    app_loop.run_until_complete(main())
