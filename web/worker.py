import os
import subprocess
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab, schedule
from dotenv import load_dotenv
from redbeat import RedBeatSchedulerEntry

# from app.models import AlertControls
from app.logger import logger
from config import BaseConfig as CFG

import celery_config


ALERT_PERIOD = CFG.ALERT_PERIOD
UPDATE_CL_PERIOD = CFG.UPDATE_CL_PERIOD
DAILY_SUMMARY_PERIOD = CFG.DAILY_SUMMARY_PERIOD
LOGS_DELETION_PERIOD = CFG.LOGS_DELETION_PERIOD

load_dotenv()

REDIS_PORT = os.environ.get("REDIS_PORT")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_ADDR = os.environ.get("REDIS_ADDR", f"localhost:{REDIS_PORT}")
BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_ADDR}"


app = Celery(__name__)
app.conf.broker_url = BROKER_URL
app.conf.timezone = "US/Eastern"
app.conf.redbeat_redis_url = f"{BROKER_URL}/1"
app.config_from_object(celery_config)
# celery.conf.result_backend = conf.REDIS_URL_FOR_CELERY


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    logger.debug("ALERT_PERIOD: {}", ALERT_PERIOD)
    logger.debug("DAILY_SUMMARY_PERIOD: {}", DAILY_SUMMARY_PERIOD)
    logger.debug("UPDATE_CL_PERIOD: {}", UPDATE_CL_PERIOD)
    logger.debug("LOGS_DELETION_PERIOD: {}", LOGS_DELETION_PERIOD)

    # interval = crontab(hour=9, minute=0)  # hours
    # entry = RedBeatSchedulerEntry(
    #     "daily_summary", "worker.daily_summary", interval, app=app
    # )
    # entry.save()

    interval = schedule(run_every=UPDATE_CL_PERIOD)  # seconds
    entry = RedBeatSchedulerEntry(
        "update_cl_stat", "worker.update_cl_stat", interval, app=app
    )
    entry.save()

    interval = schedule(run_every=timedelta(seconds=LOGS_DELETION_PERIOD))
    entry = RedBeatSchedulerEntry(
        "clean_old_logs", "worker.clean_old_logs", interval, app=app
    )
    entry.save()

    logger.debug("Tasks added to Redis")


@app.task
def update_cl_stat():
    flask_proc = subprocess.Popen(["flask", "update-cl-stat"])
    flask_proc.communicate()


# @app.task
# def daily_summary():
#     flask_proc = subprocess.Popen(["flask", "daily-summary"])
#     flask_proc.communicate()


@app.task
def clean_old_logs():
    flask_proc = subprocess.Popen(["flask", "clean-old-logs"])
    flask_proc.communicate()


@app.task
def scan_pcc_activations(scan_record_id: int):
    flask_proc = subprocess.Popen(
        ["flask", "scan-pcc-activations", str(scan_record_id)]
    )
    flask_proc.communicate()
