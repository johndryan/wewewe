import os
from flask import Flask
import redis
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url)
import time
from datetime import datetime
from flask import Response
from flask import request

app = Flask(__name__)

ONLINE_LAST_MINUTES = 1

def mark_online(user_id):
    now = int(time.time())
    # expires = now + (app.config['ONLINE_LAST_MINUTES'] * 60) + 10
    expires = now + (ONLINE_LAST_MINUTES * 60) + 10
    all_users_key = 'online-users/%d' % (now // 60)
    user_key = 'user-activity/%s' % user_id
    p = redis.pipeline()
    p.sadd(all_users_key, user_id)
    p.set(user_key, now)
    p.expireat(all_users_key, expires)
    p.expireat(user_key, expires)
    p.execute()

def get_user_last_activity(user_id):
    last_active = redis.get('user-activity/%s' % user_id)
    if last_active is None:
        return None
    return datetime.utcfromtimestamp(int(last_active))

def get_online_users():
    current = int(time.time()) // 60
    minutes = xrange(ONLINE_LAST_MINUTES)
    return redis.sunion(['online-users/%d' % (current - x)
                         for x in minutes])

@app.before_request
def mark_current_user_online():
    mark_online(request.remote_addr)

@app.route('/')
def index():
    return Response('Online: %s' % ', '.join(get_online_users()),
                    mimetype='text/plain')

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)