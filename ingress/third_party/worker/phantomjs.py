from celery import Celery
import subprocess
app = Celery('phantomjs')
app.conf.update(
    broker_url = 'amqp://guest@rabbit',
    result_backend = 'amqp://guest@rabbit',
)
@app.task
def get_cookie(email, password):
    """ params: email,password
    return: json string
    {
      "status":"success",
      "data":
        {"SACSID":"",
         "csrftoken":"",
         "payload_v":""
        }
    }
    """
    pass

