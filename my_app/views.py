
import pandas as pd
from flask import render_template, request, redirect, make_response, session
from my_app import app, auth
from stravalib import Client

app.secret_key = 'DONTCAREWHATTHISIS'

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
  if request.method == 'GET':
      return render_template('welcome.html',num=10)
  else:
      return redirect('/result')
      #return redirect('/main')
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
  return athlete.firstname + ' ' + athlete.lastname

@app.route("/result", methods=['GET'])
def results_table():
  # get the rivals data frame
  rivals = nearest_rivals_from_file()
  # put in list of lists
  rivals_list = zip(rivals['athlete_name'], rivals['counts'], rivals.index.tolist())
  return render_template('result.html', table_rows = rivals_list)


def nearest_rivals_from_file():
  '''get nearest rivals from file'''
  rivals = pd.DataFrame.from_csv('my_app/test_data/sorted_counts.csv')
  return rivals[1:20]

def nearest_rivals():
  return
