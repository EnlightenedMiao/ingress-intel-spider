import os
import logging
import time
import json
import requests
from django.conf import settings
from ingress.ingress.models import Account
import re
from bs4 import BeautifulSoup

def load_cookies():
    """return a list which has one or zero account
    """
    return Account.objects.filter(is_valid=True)[:1]

def plain_login():
    s = requests.Session()
    r = s.get('https://www.ingress.com/intel')
    if r.status_code != 200:
        logging.error('Could not connect to intel web')
        return None
    else:
        soup = BeautifulSoup(r.text)
        login_link = soup.find('a')['href']
        if login_link == '':
            logging.error('Could not find login link in index')
        s = google_login(s,login_link)
        

def get_plexts(timems):
    valid_account = load_cookies()
    if not valid_account:
        logging.error('No valid account available')
        return {}
    else:
        valid_account=valid_account[0]
        COOKIES = {
            "SACSID":valid_account.ingress_SACSID,
            "csrftoken":valid_account.ingress_csrf_token,
        }
        spider_session = requests.Session()
        AREA_LINK = "https://www.ingress.com/intel?ll=40.199855,116.38916&z=8"
        r = spider_session.get(AREA_LINK,cookies=COOKIES)
        
        
        if r.status_code != 200:
            logging.error('cookie invalid')
            valid_account.is_valid=False
            valid_account.save()
            return {}
        valid_account.ingress_csrf_token = r.cookies['csrftoken']
        version_match = re.search(r'/jsc/gen_dashboard_(\w*)', r.text) 
        PAYLOAD_V = version_match.group(1)
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
            "v": PAYLOAD_V,

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
