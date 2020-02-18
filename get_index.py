#! /usr/bin/env python3
#
# Gets index price and register it to database.
#
# The format of the saved data is bellow.
#
#   - database: bitmex
#   - measurement: index
#   - tags: ['symbol']
#   - fields: ['value']
#
# Args:
#   1. InfluxDB hostname that data is saved
#   2. Index symbol [.BXBT, .BETH, .BETHXBT, .BXRPXBT, .BBCHXBT, .BLTCXBT,
#     .BEOSXBT, .BADAXBT, .BTRXXBT]
#
# Note:
#   Parameters are able to replace by environment variables. This mechanism is
#   for performing as the AWS Lambda function.
#   if you use this mechanism, you need to define following variables.
#
#   1. INFLUXDB_HOST: Same as argv[1]
#   2. SYMBOL: Same as argv[2]
#
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

import requests
from influxdb import InfluxDBClient

VAR_INFLUXDB_HOST: str = 'INFLUXDB_HOST'  # Environment variable name: InfluxDB hostname
VAR_SYMBOL: str = 'SYMBOL'  # Environment variable name: Crypto-currency symbol name
BASE_URL: str = 'https://www.bitmex.com/api/v1'  # Rest API base URL


def get_trade(symbol: str = 'XBTUSD',
              start_time: datetime = datetime.now(tz=timezone.utc),
              count: int = 10) -> Dict[str, Any]:
    """
    Returns the trade of symbol since date as specified 'start_date'.

    :param symbol: crypto-currency symbol
    :param start_time: point starting
    :param count: number of trade
    :return: the return value of rest api '/trade'
    """
    res = requests.get(url=BASE_URL + '/trade',
                       params={
                           'symbol': symbol,
                           'startTime': start_time,
                           'count': count,
                       })
    return json.loads(res.content.decode("utf-8")) if len(res.content) > 0 else ''


def write(trades: List[Dict[str, Any]], host: str) -> bool:
    """
    Write trades to InfluxDB as index.

    :param trades: the trade data obtained REST API
    :return: True, if operation is successful
    """
    points: List[Dict[str, Any]] = []
    for t in trades:
        points.append({
            'measurement': 'index2',
            'time': t['timestamp'],
            'tags': {
                'symbol': t['symbol']
            },
            'fields': {
                'value': t['price']
            }
        })
    client: InfluxDBClient = InfluxDBClient(host=host)
    print(f'Write points: {points}')
    return client.write_points(database='bitmex', points=points)


def main(host: str = os.getenv(VAR_INFLUXDB_HOST), symbol: str = os.getenv(VAR_SYMBOL)):
    count = 3
    print(f'Parameters: host={host}, symbol={symbol}')
    start_time = datetime.now(tz=timezone.utc) - timedelta(minutes=count)
    print(f'Get the trade over past {count} minutes.')
    trades = get_trade(symbol=symbol, start_time=start_time, count=count)
    print('Write the trade to InfluxDB as index.')
    result = write(trades, host)
    if not result:
        raise Exception('Failed to write the index.')
    print('Done')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("usage: get_index.py influxdb_host symbol")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
