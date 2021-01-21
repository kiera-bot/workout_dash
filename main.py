import pandas
from datetime import datetime, timedelta
from time import time #dont think im using this anymore
from pprint import pprint
from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from absl import flags
from peloton_client import peloton_client

app = Flask(__name__)

client = peloton_client.PelotonClient(username="banana",
                                      password="anotherbanana")


# needs optimization pass
# today's stats are borked

def get_challenge_data():

  my_stats = client.fetch_user_data()
  my_stats = my_stats[0]
  my_challenges = client.fetch_user_challenges_current()
  current_stats = extract_challenge_data(my_challenges.get('challenges'))

  now = datetime.now() #datetime.now seems kinda slow. putting it here to only call once.
  current_month = now.strftime('%B') #strftime sure seems slow too. maybe even slower than .now
  current_year = now.strftime('%Y') #these seem to be the bottlenecks. will need to test.
  last_month = now.replace(day=1) - timedelta(1)

  my_challenges_past = client.fetch_user_challenges_past()
  past_stats = extract_past_challenge_data(my_challenges_past.get('challenges'))

  this_month_miles = current_stats.get('%s Cycling Challenge' %current_month)
  annual_miles = calculate_year_miles(my_challenges_past.get('challenges'))
  annual_miles += this_month_miles
  

  output_dict = {
    'all_rides': my_stats.get('total_pedaling_metric_workouts'),
    'week_streak': my_stats.get('streaks').get('current_weekly'),
    'annual_minutes': current_stats.get('The Annual %s' %current_year) ,
    'this_month_active': current_stats.get('%s Activity Challenge' %current_month),
    'this_month_miles': this_month_miles,
    'annual_miles': annual_miles,
    'last_month_active': past_stats.get('%s Activity Challenge' %last_month.strftime('%B')),
    'last_month_miles': past_stats.get('%s Cycling Challenge' %last_month.strftime('%B')),
    }
  # print(output_dict)
  return output_dict
  



  
    # forty_days_ago = datetime.now().timestamp() - 3456000
    # my_stats = client.fetch_user_data()
    # my_stats = my_stats[0]
    # all_bike_rides = my_stats.get('total_pedaling_metric_workouts')
    # week_streak = my_stats.get('streaks').get('current_weekly')

    # my_challenges = client.fetch_user_challenges_current()
    # current_progress = my_challenges.get('challenges')
    # for c in current_progress:
    #     if 'Annual' in c.get('challenge_summary').get('title'):
    #         annual_minutes = c.get('progress').get('metric_display_value')
    #     elif 'Cycling Challenge' in c.get('challenge_summary').get('title'):
    #         this_month_miles = c.get('progress').get('metric_display_value')
    #     elif 'Activity Challenge' in c.get('challenge_summary').get('title'):
    #         this_month_active = c.get('progress').get('metric_display_value')
    #     else:
    #         pass

    # my_challenges_past = client.fetch_user_challenges_past()
    # year_sum = 0
    # past = my_challenges_past.get('challenges')
    # for p in past:
    #     if 'Cycling Challenge' in p.get('challenge_summary').get(
    #             'title'
    #     ) and p.get('challenge_summary').get('start_time') >= 1609459200:
    #         year_stats = p.get('progress').get('metric_display_value')
    #         year_sum += int(float(year_stats))
    #     elif 'Activity Challenge' in p.get('challenge_summary').get(
    #             'title'
    #     ) and p.get('challenge_summary').get('end_time') >= forty_days_ago:
    #         last_month_active = p.get('progress').get('metric_display_value')
    #     else:
    #         pass
    # year_sum += int(float(this_month_miles))



def extract_data(input_data):
    output_dict = {}
    for x in input_data:
        output_dict[x.get('slug')] = x.get('value')
    return output_dict


def extract_challenge_data(input_data):
    output_dict = {}
    for x in input_data:
        output_dict[x.get('challenge_summary').get('title')] = x.get('progress').get('metric_value')
    return output_dict    


def extract_past_challenge_data(input_data):
    output_dict = {}
    for x in input_data:
      if x.get('challenge_summary').get('end_time') >= datetime.now().timestamp() - 31536000:
        output_dict[x.get('challenge_summary').get('title')] = x.get('progress').get('metric_value')
      else:
        pass
    return output_dict


def calculate_year_miles(input_data):
    meh = datetime.now().replace(month =1, day=1, hour=0, minute=0,second=0, microsecond=0).timestamp()
    year_sum = 0
    for x in input_data:
      if x.get('challenge_summary').get('end_time') >= meh and 'Cycling Challenge' in x.get('challenge_summary').get('title'):
        year_sum += x.get('progress').get('metric_value')
      else:
        pass
    return year_sum


def get_today_data():
  # Need to write in logic in case there is no data for the day
  # hmmmmmmm this is not adding up correctly. Something is borked with pandas.to_datetime('today').normalize() see line 138
    workouts = client.fetch_workouts()
    workouts_df = pandas.DataFrame(workouts)
    workouts_df['created_at'] = pandas.to_datetime(workouts_df['created_at'],unit='s')
    print(workouts_df)
    today_mask = (workouts_df.created_at >= pandas.to_datetime('today').normalize())
    test = pandas.to_datetime('today').normalize()
    print(test)
    print(today_mask)
    workouts_df = workouts_df.loc[today_mask]
    print(workouts_df)
    workouts = [
        client.fetch_workout_metrics(x) for x in workouts_df.id.to_list()
    ]
    workout_metrics_df = pandas.DataFrame(workouts)
    summary = workout_metrics_df['summaries']
    print(summary)
    average_summary = workout_metrics_df['average_summaries']
    core_metrics_df = summary.apply(extract_data)
    core_metrics_df = core_metrics_df.apply(pandas.Series)
    core_averages_df = average_summary.apply(extract_data)
    core_averages_df = core_averages_df.apply(pandas.Series)


    output_dict = {
        'distance': round(core_metrics_df.distance.sum(), 0),
        'output': core_metrics_df.total_output.sum(),
        'cals': core_metrics_df.calories.sum(),
        'speed': round(core_averages_df.avg_speed.mean(), 0),
        'duration': round(workouts_df.total_video_watch_time_seconds.sum() / 60, 0),
    }
    return output_dict

    # today_mask = (workout_df['created_at'] >=
    #               pandas.to_datetime('today').normalize())
    # workout_today_df = workout_df.loc[today_mask]
    # workouts_today = [
    #     client.fetch_workout_metrics(x) for x in workout_today_df.id.to_list()
    # ]
    # if workouts_today == []:
    #     today_cals = 0
    #     today_output = 0
    #     today_distance = 0
    #     today_duration = 0
    #     today_speed = 0
    # else:
    #     today_duration = workout_today_df.total_video_watch_time_seconds.sum()
    #     today_duration = today_duration / 60
    #     today_duration = round(today_duration, 2)
    #     workout_metrics_today_df = pandas.DataFrame(workouts_today)
    #     today_summary = workout_metrics_today_df['summaries']
    #     today_avg_summary = workout_metrics_today_df['average_summaries']
    #     today_core_metrics_df = today_summary.apply(extract_data)
    #     today_core_metrics_df = today_core_metrics_df.apply(pandas.Series)
    #     today_avg_core_metrics_df = today_avg_summary.apply(extract_data)
    #     today_avg_core_metrics_df = today_avg_core_metrics_df.apply(
    #         pandas.Series)
    #     today_avg_speed = today_avg_core_metrics_df.avg_speed.mean()
    #     today_avg_speed = round(today_avg_speed, 2)
    #     today_cals = today_core_metrics_df.calories.sum()
    #     today_output = today_core_metrics_df.total_output.sum()
    #     today_distance = today_core_metrics_df.distance.sum()
    #     print(today_distance)
    


def get_last_workout_data():
    workouts = client.fetch_workouts(limit=1)
    last_workout = workouts[0]
    last_workout_metrics = client.fetch_workout_metrics(last_workout.get('id'))
    
    last_workout_core_stats = extract_data(
        last_workout_metrics.get('summaries'))
   
    last_workout_core_averages = extract_data(
        last_workout_metrics.get('average_summaries'))

    output_dict = {
        'distance': last_workout_core_stats.get('distance'),
        'output': last_workout_core_stats.get('total_output'),
        'cals': last_workout_core_stats.get('calories'),
        'speed': last_workout_core_averages.get('avg_speed'),
        'duration': last_workout.get('ride').get('duration') / 60,
        'title': last_workout.get('ride').get('title'),
    }
    # print(output_dict)
    return output_dict
    # last_distance = None
    # last_output = None
    # last_cals = None
    # last_speed = None
    # last_workout = workouts[0]
    # last_workout_id = last_workout.get('id')
    # last_duration = last_workout.get('ride').get('duration')
    # last_duration = last_duration / 60
    # last_title = last_workout.get('ride').get('title')
    # last_workout_metrics = client.fetch_workout_metrics(last_workout_id)
    # last_summaries = last_workout_metrics.get('summaries')
    # last_avg_summaries = last_workout_metrics.get('average_summaries')
    # for average in last_avg_summaries:
    #     if average.get('slug') == 'avg_speed':
    #         last_speed = average.get('value')
    #     else:
    #         pass
    # for summary in last_summaries:
    #     if summary.get('slug') == 'distance':
    #         last_distance = summary.get('value')
    #     elif summary.get('slug') == 'total_output':
    #         last_output = summary.get('value')
    #     elif summary.get('slug') == 'calories':
    #         last_cals = summary.get('value')
    #     else:
    #         pass
    # return last_workout_data


@app.route('/')
def index():

    #run the functions. pass the data through the render template.
    last_workout = get_last_workout_data()
    today_workout = get_today_data()
    challenge_stats = get_challenge_data()
    # pprint(workout_stats)

    return render_template("index.html", last_workout=last_workout, today_workout=today_workout, challenge_stats=challenge_stats)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
