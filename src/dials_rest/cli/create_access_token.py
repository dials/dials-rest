import argparse

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
    token = create_access_token({}, expires=args.expiry)
    print(token)
