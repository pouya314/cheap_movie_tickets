import datetime
import decimal
import itertools
import json
import os
import requests
from worker import redis_conn


class MaxRetryReachedError(Exception): pass


def make_request_with_retry(url, headers, retries=5):
    attempt = 1
    while attempt <= retries:
        print('(Attempt#{}) API CALL => {}'.format(attempt, url))
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        attempt += 1
    raise MaxRetryReachedError('Maximum retries limit of {} reached.'.format(retries))


def get_fresh_movie_data():
    """
    Fetch fresh movie data thru API calls.
    """
    print('get_fresh_movie_data(): START')

    sources = ['filmworld', 'cinemaworld']
    
    auth_headers = {'x-access-token': os.environ['X_ACCESS_TOKEN']}
    all_movies_url = 'http://webjetapitest.azurewebsites.net/api/{source}/movies' 
    single_movie_url = 'http://webjetapitest.azurewebsites.net/api/{source}/movie/{movie_id}'
    
    al = []
    for src in sources:
        movies = make_request_with_retry(all_movies_url.format(source=src), 
            auth_headers)['Movies']
        for movie in movies:
            movie_id = movie['ID']
            uuid = movie_id[2:]
            m = make_request_with_retry(single_movie_url.format(source=src, 
                movie_id=movie_id), auth_headers)
            m['Price'] = '{:.2f}'.format(decimal.Decimal(m['Price']))
            m.update({'Source': src})
            m.update({'UUID': uuid})
            al.append(m)

    redis_entry = {
        'movies': [],
        'updated_at': datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S (%Z)')
    }
    sorted_al = sorted(al, key=lambda x: x['UUID'])
    for uuid, group in itertools.groupby(sorted_al, lambda x: x['UUID']):
        min_found = min(list(group), key=lambda x: decimal.Decimal(x['Price']))
        redis_entry['movies'].append(min_found)

    # save result in redis
    redis_conn.set('movies', json.dumps(redis_entry))

    print('get_fresh_movie_data(): END')


if __name__ == '__main__':
    get_fresh_movie_data()