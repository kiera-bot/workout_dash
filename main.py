from absl import app, flags
from google.cloud import bigquery

from peloton_client import peloton_client

FLAGS = flags.FLAGS
flags.DEFINE_string('peloton_username', None, 'Your Peloton username.')
flags.DEFINE_string('peloton_password', None, 'Your Peloton password.')
flags.DEFINE_string('table_id', None, 'The BigQuery table name to store data.')
flags.mark_flag_as_required('peloton_username')
flags.mark_flag_as_required('peloton_password')
flags.mark_flag_as_required('table_id')

DATASET = 'peloton'
BQ_CLIENT = bigquery.Client()  #auth
JOB_CONFIG = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")


def extract_data(input_data):
    output_dict = {}
    for x in input_data:
        output_dict[x.get('slug')] = x.get('value')
    return output_dict


def get_workout_data(workouts):
    output_workouts = []
    for workout in workouts:
        workout_metrics = PT_CLIENT.fetch_workout_metrics(workout.get('id'))

        workout_core_stats = extract_data(workout_metrics.get('summaries'))

        workout_core_averages = extract_data(
            workout_metrics.get('average_summaries'))

        output_dict = {
            'distance': workout_core_stats.get('distance'),
            'output': workout_core_stats.get('total_output'),
            'cals': workout_core_stats.get('calories'),
            'speed': workout_core_averages.get('avg_speed'),
            'duration': workout.get('ride').get('duration') / 60,
            'title': workout.get('ride').get('title'),
            'created_at': workout.get('created_at')
        }
        output_workouts.append(output_dict)
    return output_workouts


def main(argv):
    global PT_CLIENT
    PT_CLIENT = peloton_client.PelotonClient(username=FLAGS.peloton_username,
                                             password=FLAGS.peloton_password)
    workouts = PT_CLIENT.fetch_workouts(fetch_all=True)
    banana = get_workout_data(workouts)
    table_id = '%s.%s.%s' % (BQ_CLIENT.project, DATASET, FLAGS.table_id)
    job = BQ_CLIENT.load_table_from_json(banana,
                                         table_id,
                                         job_config=JOB_CONFIG)
    job.result()


if __name__ == '__main__':
    app.run(main)
