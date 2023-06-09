import argparse
import datetime

import dateutil.parser

from ..auth import create_access_token


def run(args=None):
    parser = argparse.ArgumentParser(
        "Generate an access token for the dials-rest server"
    )
    parser.add_argument(
        "--expiry",
        "-e",
        help="",
        type=dateutil.parser.parse,
    )

    args = parser.parse_args(args=args)
    if args.expiry:
        expires = datetime.datetime(
            args.expiry.year,
            args.expiry.month,
            args.expiry.day,
            args.expiry.hour,
            args.expiry.minute,
            args.expiry.second,
            tzinfo=dateutil.tz.UTC,
        )
    else:
        expires = None
    token = create_access_token({}, expires=expires)
    print(token)
