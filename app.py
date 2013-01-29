import os
from flask import Flask
import redis
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url)
import time
import random
from datetime import datetime
from datetime import timedelta
from flask import Response
from flask import request
from flask import redirect
from flask import make_response
from flask import render_template
from real_ip_address import ProxiedRequest

app = Flask(__name__)

ONLINE_LAST_MINUTES = 1
NUM_USERS_REQUIRED = 5

def mark_online(user_ip, cookie_id):
    now = int(time.time())
    expires = now + (ONLINE_LAST_MINUTES * 60) + 10
    all_users_key = 'online-users/%d' % (now // 60)
    ip_users_key = 'ip-users/%d/%s' % ((now // 60), user_ip)
    user_key = 'user-activity/%s' % cookie_id
    p = redis.pipeline()
    p.sadd(all_users_key, user_ip)
    p.sadd(ip_users_key, cookie_id)
    p.set(user_key, now)
    p.expireat(all_users_key, expires)
    p.expireat(user_key, expires)
    p.expireat(ip_users_key, expires)
    p.execute()

def get_user_last_activity(user_ip):
    last_active = redis.get('user-activity/%s' % user_ip)
    if last_active is None:
        return None
    return datetime.utcfromtimestamp(int(last_active))

def get_online_users():
    current = int(time.time()) // 60
    minutes = xrange(ONLINE_LAST_MINUTES)
    return redis.sunion(['online-users/%d' % (current - x)
                         for x in minutes])

def get_ip_users( current_ip ):
    current = int(time.time()) // 60
    minutes = xrange(ONLINE_LAST_MINUTES)
    return redis.sunion(['ip-users/%d/%s' % ((current - x), current_ip)
                         for x in minutes])

@app.before_request
def mark_current_user_online():
    cookie = request.cookies.get('existing_user')
    # Only mark session as active once the user has a cookie
    if cookie is not None:
        mark_online(request.remote_addr, cookie)

@app.route('/')
def index():
    cookie = request.cookies.get('existing_user')
    # If there's no cookie, redirect and set one. If there is, go ahead and load the page
    if cookie is None:
        return redirect('/add')
    else:
        critical_mass = NUM_USERS_REQUIRED;
        num_users = len(get_ip_users( request.remote_addr ))
        # What percentage of users present? Max is 100%
        percent = min(100 * len(get_ip_users( request.remote_addr ))/critical_mass,100)
        # if there's enough users, display. Else don't
        if len(get_ip_users( request.remote_addr )) >= NUM_USERS_REQUIRED:
            state = "unlocked"
        else:
            state = "locked"
        return render_template('index.html', **locals())

@app.route('/add')
def cookie_insertion():
    redirect_to_index = redirect('/')
    response = make_response(redirect_to_index)
    # Create random cookie id
    cookie = '%030x' % random.randrange(256**15)
    # Don't expire for a month
    expires = datetime.now() + timedelta(days=30)
    response.set_cookie('existing_user', cookie, expires=expires)
    return response
    
@app.route('/critical_mass_reached')
def critical_mass_reached():
    num_users = len(get_ip_users( request.remote_addr ))
    percent = min(100 * num_users/NUM_USERS_REQUIRED,100)
    return Response("%s,%s" % (percent,num_users), mimetype='text/plain')

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    # App debugging on
    app.debug = True
    # Workaround for Heroku Request IPs
    app.request_class = ProxiedRequest
    app.run(host='0.0.0.0', port=port)