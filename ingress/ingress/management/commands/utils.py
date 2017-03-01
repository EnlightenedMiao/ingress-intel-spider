import os
import logging
import time
import json
import requests
from django.conf import settings
from ingress.ingress.models import Account
import re
from bs4 import BeautifulSoup
from third_party.worker import phantomjs

def load_cookies():
    """return a list which has one or zero account
    """
    return Account.objects.filter(is_valid=True)[:1]

def refresh_cookie(account_id):
    ingress_account = Account.objects.get(id=account_id)
    async_result = phantomjs.get_cookie(account.google_username,account.google_password)
    # 后期可以改为异步的做法，让phantom的worker直接更新数据库里的cookie 
    timeout= 100
    job_time = 0
    while async_result.ready() is False :
        timestart+=10
        if job_time > timeout:
            return {'error':'job timeout'}
        time.sleep(10)
    if async_result.successful():
        result = json.loads(async_result.result)
        ingress_account.ingress_SACSID = result['SACSID']
        ingress_account.ingress_csrf_token = result['csrftoken']
        ingress_account.payload_v = result['payload_v']
        ingress_account.save()
        return True

def get_plexts(timems):
    valid_account = load_cookies()
    if not valid_account:
        account_id = Account.objects.all()[0].id
        if refresh_cookie(account_id):
            valid_account = Account.objects.get(id=account_id)
        else:
            return {}
    else:
        valid_account=valid_account[0]
    COOKIES = {
        "SACSID":valid_account.ingress_SACSID,
        "csrftoken":valid_account.ingress_csrf_token,
    }
    spider_session = requests.Session()
    
    PLEXTS_LINK = "https://www.ingress.com/r/getPlexts"
    just_now = int((time.time() - 20) * 1000)
    payload = {
        "minLatE6": settings.MIN_LAT,
        "minLngE6": settings.MIN_LNG,
        "maxLatE6": settings.MAX_LAT,
        "maxLngE6": settings.MAX_LNG,
        "minTimestampMs": just_now,
        "maxTimestampMs": -1,
        "tab": "all",
        "ascendingTimestampOrder": True,
        "v": valid_account.payload_v,

    }
    payload.update({'minTimestampMs': timems})
    HEADERS = {
        "accept": "*/*",
        "accept-encoding": "gzip,deflate,sdch",
        "accept-language": "en-US,en;q=0.8,zh-TW;q=0.6",
        "cache-control": "no-cache",
        "content-length": "182",
        "content-type": "application/json; charset=UTF-8",
        "origin": "https://www.ingress.com",
        "pragma": "no-cache",
        "referer": "https://www.ingress.com/intel",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36",
        "x-csrftoken": valid_account.ingress_csrf_token,
    }
    r = spider_session.post(PLEXTS_LINK,cookies=COOKIES,data=json.dumps(payload),headers=HEADERS)
    try:
        plexts = r.json()
    except:
        valid_account.is_valid=False
        valid_account.save()
        logging.info(r.text)
        return {}
    return plexts

def get_cookie_str():
    path_cookie = os.path.join(settings.DIR_INGRESS_CONF, 'cookie.txt')
    if not os.path.exists(path_cookie):
        return settings.INGRESS_INTEL_COOKIE
    with open(path_cookie) as f:
        cookie = f.read()
    if not cookie:
        return settings.INGRESS_INTEL_COOKIE
    return cookie
COOKIE = get_cookie_str()


def get_csrf_str():
    path_csrf = os.path.join(settings.DIR_INGRESS_CONF, 'csrf.txt')
    if not os.path.exists(path_csrf):
        return settings.INGRESS_INTEL_CSRF_TOKEN
    with open(path_csrf) as f:
        csrf = f.read()
    if not csrf:
        return settings.INGRESS_INTEL_CSRF_TOKEN
    return csrf
CSRF = get_csrf_str()


def get_payload_v_str():
    path_payload_v = os.path.join(settings.DIR_INGRESS_CONF, 'payload_v.txt')
    if not os.path.exists(path_payload_v):
        return settings.INGRESS_INTEL_PAYLOAD_V
    with open(path_payload_v) as f:
        payload_v = f.read()
    if not payload_v:
        return settings.INGRESS_INTEL_PAYLOAD_V
    return payload_v


def _touch_need_update():
    os.makedirs(settings.DIR_INGRESS_CONF, exist_ok=True)
    file_need_update = os.path.join(settings.DIR_INGRESS_CONF, 'need_update.txt')
    open(file_need_update, 'w').close()


def cookie_need_update():
    file_need_update = os.path.join(settings.DIR_INGRESS_CONF, 'need_update.txt')
    return os.path.exists(file_need_update)




if __name__ == '__main__':
    just_now = int((time.time() - 20) * 1000)
    result = get_plexts(just_now)
