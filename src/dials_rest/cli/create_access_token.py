import argparse
import datetime

import dateutil.parser

from ..auth import create_access_token


def run():
    parser = argparse.ArgumentParser(
        "Generate an access token for the dials-rest server"
    )
    parser.add_argument(
        "--expiry",
        "-e",
        help="",
        type=dateutil.parser.parse,
    )

    args = parser.parse_args()
    expires = datetime.datetime(
        args.expiry.year, args.expiry.month, args.expiry.day, tzinfo=dateutil.tz.UTC
    )
    token = create_access_token({}, expires=expires)
    print(token)
