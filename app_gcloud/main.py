import pandas as pd
from flask import Flask, render_template, request, redirect, make_response, session, url_for
from stravalib import Client
import time, json, os

app = Flask(__name__)
app.secret_key = 'DONTCAREWHATTHISIS'

app.question2 = {}
app.question3 = {}
app.question2['How many of your activities do you want us to use?']=('5',\
                '10','20')
app.question3['How would you like to filter the results?']=('Females Only ',\
                                          'Males Only', 'Runs Only', 'Rides Only')

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

  access_token = getToken(MY_STRAVA_CLIENT_ID, MY_STRAVA_CLIENT_SECRET)
  if access_token == None:
      return redirectAuth(MY_STRAVA_CLIENT_ID)
  #session['access_token'] = access_token
  client = Client(access_token=session['access_token'])
  athlete = client.get_athlete() # Get current athlete details
  session['athlete_name'] = athlete.firstname + ' ' + athlete.lastname
  session['athlete_id'] = str(athlete.id)
  # segment_ids_from_activities(client, max_activities = 5) # sets segment_ids_unique
  return redirect('/options')
  #if you want a simple output of first name, last name, just use this line:
  #return athlete.firstname + ' ' + athlete.lastname

@app.route("/options", methods=['GET','POST'])
def set_options():
  # place to ask things like how many activities to use
  #render_template('waiting.html')
  session['max_activities'] = 10
  session['context_entries'] = 10

  if request.method == 'GET':
     #for clarity (temp variables)
     q = next(iter(app.question2.keys()))
     #this will return the answers corresponding to q
     [a1, a2, a3] = next(iter(app.question2.values()))
     #save the current questions key
     #app.currentq = q
     return render_template('options.html',question=q,ans1=a1,ans2=a2,ans3=a3)
  else:   #request was a POST
     #session['question3_answered'] = 1
     session['max_activities'] = int(request.form['max_choice'])
     print ('retrieving ' + str(session['max_activities']) + ' activities!')
  return redirect('/segments')

@app.route("/segments")
def retrieve_ids():
    client = Client(access_token=session['access_token'])
    segment_ids_from_activities(client, max_activities = session['max_activities'])

    with open(str(session['athlete_id'])+'segments_to_do.txt', 'w') as f:
      f.write('\n'.join(str(ids) for ids in session['segment_ids_unique']))
    tmp = {session['athlete_id']:session['athlete_name']}
    json.dump(dict(), open(session['athlete_id']+'segment_rivals.json','w'))
    json.dump(dict(), open(session['athlete_id']+'athlete_names.json','w'))

    return redirect("/waiting")

@app.route("/waiting", methods=['GET','POST'])
def segments_by_chunk():
  print('starting another chunk!')
  with open(str(session['athlete_id'])+'segments_to_do.txt', 'r') as f:
    segment_ids_todo = f.read().splitlines()
  segment_rivals = json.load(open(str(session['athlete_id'])+'segment_rivals.json'))
  athlete_names = json.load(open(str(session['athlete_id'])+'athlete_names.json'))
  chunk_size = 10
  client = Client(access_token=session['access_token'])
  # loop over chunks of segments
  j = 0
  if len(segment_ids_todo) < chunk_size:
    chunk_size = len(segment_ids_todo)
  for segment_id in segment_ids_todo[0:chunk_size]:
    try:
        leaderboard = client.get_segment_leaderboard(segment_id = segment_id,
                                                     top_results_limit=1,
                                                     context_entries=session['context_entries'])
        print('on segment {}; {} to go'.format(segment_id,  len(segment_ids_todo)))
    except:
        # janky error handling, should specify http error -- probably need urllib2
        print('whoops, error on {}; {} to go'.format(segment_id,  len(segment_ids_todo) ))
    j = j + 1

    segment_ids_todo.remove(segment_id) # remove from to do list
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
    time.sleep(0.5) # avoid time out?

  json.dump(segment_rivals, open(str(session['athlete_id'])+'segment_rivals.json','w'))
  json.dump(athlete_names, open(str(session['athlete_id'])+'athlete_names.json','w'))

  if (len(segment_ids_todo) > 0):
    with open(str(session['athlete_id'])+'segments_to_do.txt', 'w') as f:
      f.write('\n'.join(str(ids) for ids in segment_ids_todo))
    return redirect(url_for('segments_by_chunk', next='/'))
  else:
    return redirect('/result')



@app.route("/result")
def results_table():
  # get the rivals data frame
  #rivals = nearest_rivals_from_file()
  client = Client(access_token=session['access_token'])
  rivals = nearest_rivals(client, max_rivals = 10)
  #rivals = nearest_rivals_from_file()
  # make urls from athlete_ids
  base_url = 'https://www.strava.com/athletes/'
  urls = [base_url + str(i) for i in rivals.index.tolist()]
  # put in list of lists
  rivals_list = zip(rivals['athlete_name'], rivals['counts'], urls)
  cleanup()
  return render_template('result.html', table_rows = rivals_list)

def cleanup():
  '''remove the data files'''
  os.remove(str(session['athlete_id'])+'athlete_names.json')
  os.remove(str(session['athlete_id'])+'segment_rivals.json')
  os.remove(str(session['athlete_id'])+'segments_to_do.txt')
  return

def nearest_rivals_from_file(max_rivals = 10):
  '''get nearest rivals from file'''
  rivals = pd.DataFrame.from_csv('my_app/test_data/sorted_counts.csv')
  return rivals[1:max_rivals+1]


@app.route('/filterby',methods=['GET', 'POST'])
def filterby(): #remember the function namewaiting does not need to match th eURL
  if request.method == 'GET':
    #for clarity (temp variables)
    q = next(iter(app.question3.keys()))
    #this will return the answers corresponding to q
    [a1, a2, a3, a4] = next(iter(app.question3.values()))
    #save the current questions key
    #app.currentq = q
    return render_template('filterby.html',question=q,ans1=a1,ans2=a2,ans3=a3,ans4=a4)
  else:   #request was a POST
    #session['question3_answered'] = 1
    session['filter_choice'] = request.form['filter_choice']
    print ('filter choice is : ', session['filter_choice'])
  return redirect('/main')


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
  #segment_rivals, athlete_names = segment_leaderboards(client, context_entries = 10)
  # aggregate athletes from leaderboard context
  segment_rivals = json.load(open(str(session['athlete_id'])+'segment_rivals.json'))
  athlete_names = json.load(open(str(session['athlete_id'])+'athlete_names.json'))
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

if __name__ == "__main__":
	app.run(port=33508)
