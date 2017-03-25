import os
import logging
import time
import json
import requests
from django.conf import settings
from ingress.models import Account
import re
from bs4 import BeautifulSoup
from ingress.tasks import get_cookie

def load_cookies():
    """return a list which has one or zero account
    """
    return Account.objects.filter(is_valid=True)[:1]

def refresh_cookie(account_id):
    ingress_account = Account.objects.get(id=account_id)
    async_result = get_cookie.delay(ingress_account.google_username,ingress_account.google_password)
    # 后期可以改为异步的做法，让phantom的worker直接更新数据库里的cookie 
    timeout= 100
    job_time = 0
    while async_result.ready() is False :
        job_time+=10
        if job_time > timeout:
            return {'error':'job timeout'}
        time.sleep(10)
    if async_result.successful():
        result = json.loads(async_result.result)
        ingress_account.ingress_SACSID = result['data']['SACSID']
        ingress_account.ingress_csrf_token = result['data']['csrftoken']
        ingress_account.ingress_payload_v = result['data']['payload_v']
        ingress_account.is_valid = True
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
        "v": valid_account.ingress_payload_v,

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
        if 'result' not in plexts:
            valid_account.is_valid=False
            valid_account.save()
            # 实际上，我并不知道这里递归会不会有问题，暂时这么写吧
            return get_plexts(timems)
    except:
        valid_account.is_valid=False
        valid_account.save()
        logging.info(r.text)
        return {}
    return plexts


if __name__ == '__main__':
    just_now = int((time.time() - 20) * 1000)
    result = get_plexts(just_now)
