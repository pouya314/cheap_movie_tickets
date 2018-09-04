import os
import redis
from rq import Worker, Queue, Connection
import settings


listen = [settings.QUEUE_NAME]
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_conn = redis.from_url(redis_url)


if __name__ == '__main__':
    with Connection(redis_conn):
        worker = Worker(map(Queue, listen))
        worker.work()
