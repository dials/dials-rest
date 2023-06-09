from calendar import timegm
from datetime import datetime

import jose.jwt
from dateutil.tz import UTC


def test_create_access_token_default_expiry_time(access_token, capsys):
    from dials_rest import auth
    from dials_rest.cli import create_access_token

    create_access_token.run(args=[])
    captured = capsys.readouterr()
    token = captured.out.strip()
    data = jose.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    exp = data["exp"]
    now = timegm(datetime.utcnow().utctimetuple())
    assert exp - now <= auth.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def test_create_access_token_user_expiry_time(access_token, capsys):
    from dials_rest import auth
    from dials_rest.cli import create_access_token

    now = timegm(datetime.utcnow().utctimetuple())
    delta = 30
    expiry = datetime.fromtimestamp(now + delta, tz=UTC)
    create_access_token.run(args=["--expiry", expiry.isoformat()])
    captured = capsys.readouterr()
    token = captured.out.strip()
    data = jose.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    exp = data["exp"]
    assert exp - now <= delta
