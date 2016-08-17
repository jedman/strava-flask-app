from flask import render_template, request, redirect
from my_app import app, auth
from stravalib import Client

app.secret_key = 'DONTCAREWHATTHISIS'

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
  if request.method == 'GET':
      return render_template('welcome.html',num=10)
  else:
      return redirect('/main')
  #return auth.test_print('hi there human')

@app.route('/main')
def main():
  with open('secrets.txt') as f:
    MY_STRAVA_CLIENT_ID = f.readline().strip()
    MY_STRAVA_CLIENT_SECRET = f.readline().strip()

  access_token = auth.getToken(MY_STRAVA_CLIENT_ID,MY_STRAVA_CLIENT_SECRET)
  if access_token == None:
      return auth.redirectAuth(MY_STRAVA_CLIENT_ID)
  client = Client(access_token=access_token)
  athlete = client.get_athlete() # Get current athlete details
  #if you want a simple output of first name, last name, just use this line:
  #return athlete.firstname + ' ' + athlete.lastname
  #now get most recent activity for this athlete...
  print('athlete:', athlete.firstname, athlete.lastname)
  names = []
  maps = []
  for a in client.get_activities(before = "2016-08-16T00:00:00Z",  limit=1):
      names.append(a.name)
      maps.append(a.map)
  # another simple output for this bit is to return the name of the route
  return names[0]
