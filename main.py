from datetime import datetime, timedelta
from pprint import pprint

import pandas
from absl import app, flags, logging
from flask import Flask, redirect, render_template, request, url_for

from peloton_client import peloton_client

FLASK_APP = Flask(__name__)

# Change this to take username / password from flags
# https://abseil.io/docs/python/guides/flags
# https://docs.python.org/3/library/argparse.html
FLAGS = flags.FLAGS
flags.DEFINE_string('peloton_username', 'none', 'Your Peloton username.')
flags.DEFINE_string('peloton_password', 'none', 'Your Peloton password.')


def get_challenge_data():
    my_stats = CLIENT.fetch_user_data()
    my_stats = my_stats[0]
    my_challenges = CLIENT.fetch_user_challenges_current()
    current_stats = extract_challenge_data(my_challenges.get('challenges'))

    now = datetime.now(
    )  #datetime.now seems kinda slow. putting it here to only call once.
    current_month = now.strftime(
        '%B')  #strftime sure seems slow too. maybe even slower than .now
    current_year = now.strftime(
        '%Y')  #these seem to be the bottlenecks. will need to test.
    last_month = now.replace(day=1) - timedelta(1)

    my_challenges_past = CLIENT.fetch_user_challenges_past()
    past_stats = extract_past_challenge_data(
        my_challenges_past.get('challenges'))

    this_month_miles = current_stats.get('%s Cycling Challenge' %
                                         current_month)
    annual_miles = calculate_year_miles(my_challenges_past.get('challenges'))
    annual_miles += this_month_miles

    output_dict = {
        'all_rides':
        my_stats.get('total_pedaling_metric_workouts'),
        'week_streak':
        my_stats.get('streaks').get('current_weekly'),
        'annual_minutes':
        current_stats.get('The Annual %s' % current_year),
        'this_month_active':
        current_stats.get('%s Activity Challenge' % current_month),
        'this_month_miles':
        this_month_miles,
        'annual_miles':
        annual_miles,
        'last_month_active':
        past_stats.get('%s Activity Challenge' % last_month.strftime('%B')),
        'last_month_miles':
        past_stats.get('%s Cycling Challenge' % last_month.strftime('%B')),
    }
    return output_dict


def extract_data(input_data):
    output_dict = {}
    for x in input_data:
        output_dict[x.get('slug')] = x.get('value')
    return output_dict


def extract_challenge_data(input_data):
    output_dict = {}
    for x in input_data:
        output_dict[x.get('challenge_summary').get('title')] = x.get(
            'progress').get('metric_value')
    return output_dict


def extract_past_challenge_data(input_data):
    output_dict = {}
    for x in input_data:
        if x.get('challenge_summary').get(
                'end_time') >= datetime.now().timestamp() - 31536000:
            output_dict[x.get('challenge_summary').get('title')] = x.get(
                'progress').get('metric_value')
        else:
            pass
    return output_dict


def calculate_year_miles(input_data):
    this_year = datetime.now().replace(month=1,
                                       day=1,
                                       hour=0,
                                       minute=0,
                                       second=0,
                                       microsecond=0).timestamp()
    year_sum = 0
    for x in input_data:
        if x.get('challenge_summary').get(
                'end_time') >= this_year and 'Cycling Challenge' in x.get(
                    'challenge_summary').get('title'):
            year_sum += x.get('progress').get('metric_value')
        else:
            pass
    return year_sum


def get_today_data():
    workouts = CLIENT.fetch_workouts()
    workouts_df = pandas.DataFrame(workouts)
    today_mask = workouts_df.created_at >= datetime.now().replace(
        hour=0, minute=0, second=0).timestamp()
    print(workouts_df)

    try:
        workouts_df = workouts_df.loc[today_mask]
        print(workouts_df)
        workouts = [
            CLIENT.fetch_workout_metrics(x) for x in workouts_df.id.to_list()
        ]
        workout_metrics_df = pandas.DataFrame(workouts)
        summary = workout_metrics_df['summaries']
        average_summary = workout_metrics_df['average_summaries']
        core_metrics_df = summary.apply(extract_data)
        core_metrics_df = core_metrics_df.apply(pandas.Series)
        core_averages_df = average_summary.apply(extract_data)
        core_averages_df = core_averages_df.apply(pandas.Series)

        output_dict = {
            'distance':
            round(core_metrics_df.distance.sum(), 0),
            'output':
            core_metrics_df.total_output.sum(),
            'cals':
            core_metrics_df.calories.sum(),
            'speed':
            round(core_averages_df.avg_speed.mean(), 0),
            'duration':
            round(workouts_df.total_video_watch_time_seconds.sum() / 60, 0),
        }
    except:
        print("no data today")
        output_dict = {}
    return output_dict


def get_last_workout_data():
    workouts = CLIENT.fetch_workouts(limit=1)
    last_workout = workouts[0]
    last_workout_metrics = CLIENT.fetch_workout_metrics(last_workout.get('id'))

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
    return output_dict


@FLASK_APP.route('/')
def index():
    last_workout = get_last_workout_data()
    # pprint(last_workout)
    # raise Exception
    today_workout = get_today_data()
    challenge_stats = get_challenge_data()

    return render_template(
        "index.html",
        last_workout=last_workout,
         today_workout=today_workout,
         challenge_stats=challenge_stats,
    )

def main(argv):
    print(FLAGS.peloton_username)
    print(FLAGS.peloton_password)
    global CLIENT
    CLIENT = peloton_client.PelotonClient(username=FLAGS.peloton_username,
                                      password=FLAGS.peloton_password)
    FLASK_APP.run(host='127.0.0.1', port=8080, debug=True)

if __name__ == '__main__':
    app.run(main)
