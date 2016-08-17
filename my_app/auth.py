from flask import session, request, redirect
from stravalib import Client

def redirectAuth(MY_STRAVA_CLIENT_ID):
    client = Client()
    url = client.authorization_url(client_id=MY_STRAVA_CLIENT_ID,
                                   redirect_uri=request.url)
    return redirect(url)


def getToken(MY_STRAVA_CLIENT_ID,MY_STRAVA_CLIENT_SECRET ):
    access_token = session.get('access_token')
    if access_token != None:
        return access_token
    # the code is in the results thingy!
    code = request.args.get('code')
    if code == None:
        return None
    client = Client()
    access_token = client.exchange_code_for_token(client_id=MY_STRAVA_CLIENT_ID,\
                                                  client_secret=MY_STRAVA_CLIENT_SECRET,\
                                                  code=code)
    session['access_token'] = access_token
    return access_token


def test_print(this):
  '''make sure the imports are good'''
  if type(this) == str:
    return this
  else:
    return "hello world"
