import json
import redis
from flask import Flask, render_template, jsonify
from jobs import get_fresh_movie_data
from rq import Queue
from rq.job import Job
from rq.registry import StartedJobRegistry
from worker import redis_conn
import settings


app = Flask(__name__)

queue = Queue(settings.QUEUE_NAME, connection=redis_conn)


@app.route("/")
def index():
    return render_template('index.html')


def return_data_from_redis():
    return json.loads(redis_conn.get('movies').decode())


def cheap_ticket_data_available():
    return True if 'movies' in [key.decode() for key in redis_conn.keys()] else False


@app.route('/get_cheapest_tickets', methods = ["GET"])
def get_cheapest_tickets():
    result = return_data_from_redis() if cheap_ticket_data_available() else None
    return jsonify(result=result)


@app.route('/request_fresh_data', methods=['POST']) 
def request_fresh_data(): 
    registry = StartedJobRegistry(settings.QUEUE_NAME, connection=redis_conn) 
    running_job_ids = registry.get_job_ids()

    if len(running_job_ids) == 0: # no job currently running
        job = queue.enqueue(get_fresh_movie_data)
        job_id = job.id
    else:
        job_id = running_job_ids.pop()

    return jsonify(job_id=job_id)


@app.route('/get_job_status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    job = Job.fetch(job_id, connection=redis_conn)
    if job.is_failed:
        status = 'fail'
    elif job.is_finished:
        status = 'success'
    else:
        status = 'pending'
    return jsonify(status=status)
