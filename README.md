A simple flask app using the Strava API. 

Based on the segments you've run recently, the app uses the strava leaderboards to find your local rivals-- athletes who traverse similar segments, at similar speeds to you. 

To get started, create a virtual environment using the environment.yaml file
For example, using conda: 
conda env create -f environment.yml 

Then, type 
source activate strava-flask 

and

python run.py

A flask app should be running at 127.0.0.1:5000 

