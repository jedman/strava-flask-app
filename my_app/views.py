
import pandas as pd
from flask import render_template, request, redirect, make_response, session
from my_app import app, auth
from stravalib import Client

app.secret_key = 'DONTCAREWHATTHISIS'

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def index():
  if request.method == 'GET':
      return render_template('welcome.html')
  else:
      return redirect('/main')

@app.route('/main')
def main():
  with open('secrets.txt') as f:
    MY_STRAVA_CLIENT_ID = f.readline().strip()
    MY_STRAVA_CLIENT_SECRET = f.readline().strip()

  access_token = auth.getToken(MY_STRAVA_CLIENT_ID, MY_STRAVA_CLIENT_SECRET)
  if access_token == None:
      return auth.redirectAuth(MY_STRAVA_CLIENT_ID)
  #session['access_token'] = access_token
  client = Client(access_token=session['access_token'])
  athlete = client.get_athlete() # Get current athlete details
  session['athlete_name'] = athlete.firstname + ' ' + athlete.lastname
  # segment_ids_from_activities(client, max_activities = 5) # sets segment_ids_unique
  return redirect('/options')
  #if you want a simple output of first name, last name, just use this line:
  #return athlete.firstname + ' ' + athlete.lastname

@app.route("/options", methods=['GET','POST'])
def set_options():
  # place to ask things like how many activities to use
  #render_template('waiting.html')
  session['max_activities'] = 10
  if request.method == 'GET':
      return render_template('options.html')
  else:
      return redirect('/result')

@app.route("/result")
def results_table():
  # get the rivals data frame
  #rivals = nearest_rivals_from_file()
  client = Client(access_token=session['access_token'])

  segment_ids_from_activities(client, max_activities = session['max_activities']) # sets segment_ids_unique

  rivals = nearest_rivals(client, max_rivals = 10)
  #rivals = nearest_rivals_from_file()
  # make urls from athlete_ids
  base_url = 'https://www.strava.com/athletes/'
  urls = [base_url + str(i) for i in rivals.index.tolist()]
  # put in list of lists
  rivals_list = zip(rivals['athlete_name'], rivals['counts'], urls)
  return render_template('result.html', table_rows = rivals_list)

def nearest_rivals_from_file(max_rivals = 10):
  '''get nearest rivals from file'''
  rivals = pd.DataFrame.from_csv('my_app/test_data/sorted_counts.csv')
  return rivals[1:max_rivals+1]

def segment_ids_from_activities(client, max_activities = 5):
  # get segment ids from most recent runs
  segment_ids = []
  for a in client.get_activities( limit = max_activities ):
    # this is jank but I can't pass include_all_efforts to get_activities
    activity = client.get_activity(a.id, include_all_efforts = True) # return all segment efforts
    for effort in activity.segment_efforts:
      segment_ids.append(effort.segment.id)

  session['segment_ids_unique'] = list(set(segment_ids))
  session['uniques'] = len(session['segment_ids_unique'])
  return

def nearest_rivals(client,  max_rivals = 10):
  '''find the most similar runners based on most segments in common '''

  # get the leaderboards for all unique segments
  segment_rivals, athlete_names = segment_leaderboards(client, context_entries = 10)

  # aggregate athletes from leaderboard context
  df = pd.DataFrame.from_dict(segment_rivals, orient = 'index')
  athlete_counts = df.count().to_frame('counts')
  athlete_counts.index.name='athlete_id'

  # make a frame with the names and ids
  names = pd.Series(athlete_names).to_frame('athlete_name')

  names.index.name = 'athlete_id'
  # join the frames
  rival_counts = pd.merge(athlete_counts, names, how = 'inner', left_index = True, right_index = True)
  rival_counts.index.name = 'athlete_id'
  # and sort
  rival_counts = rival_counts.sort_values('counts', ascending=False)
  return rival_counts[1: max_rivals + 1] # strip off first entry, which is client athlete


def segment_leaderboards(client, context_entries = 10):
  '''get a dictionary with segment_id as key, with all the nearby athletes in a dict'''
  segment_rivals = dict()
  counter = 0
  athlete_names = dict() # master table
  athlete = client.get_athlete()

  for segment_id in session['segment_ids_unique']:
      counter = counter + 1
      try:
          leaderboard = client.get_segment_leaderboard(segment_id = segment_id,
                                                       top_results_limit=1,
                                                       context_entries=context_entries)
          print('on segment {}, {} of {}'.format(segment_id, counter, session['uniques'] ))
      except:
          # janky error handling, should specify http error -- probably need urllib2
          print('whoops, error on {}, {} of {}'.format(segment_id, counter, session['uniques'] ))

      segment_athletes = dict()
      for i, entry in enumerate(leaderboard):
          # remove first entry
          # this should not be done if athlete is within context_entries of 1st
          if i == 0:
            continue
          else:
            segment_athletes[entry.athlete_id] = entry.athlete_name
            athlete_names[entry.athlete_id] = entry.athlete_name

      segment_rivals[segment_id] = segment_athletes

  return segment_rivals, athlete_names
