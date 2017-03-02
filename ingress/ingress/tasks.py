from __future__ import absolute_import, unicode_literals
from celery import Celery

app = Celery('phantomjs')

app.conf.update(broker_url = 'amqp://guest@rabbit',result_backend = 'amqp://guest@rabbit',)

@app.task(name='tasks.get_cookie')
def get_cookie(email,password):
    pass
