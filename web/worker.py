import os
import subprocess

from celery import Celery
from dotenv import load_dotenv

from app.logger import logger
from config import BaseConfig as CFG


ALERT_PERIOD = CFG.ALERT_PERIOD
UPDATE_CL_PERIOD = CFG.UPDATE_CL_PERIOD

load_dotenv()

REDIS_PORT = os.environ.get("REDIS_PORT")
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
REDIS_ADDR = os.environ.get("REDIS_ADDR", f"localhost:{REDIS_PORT}")
BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_ADDR}"

app = Celery(__name__)
app.conf.broker_url = BROKER_URL
# celery.conf.result_backend = conf.REDIS_URL_FOR_CELERY


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    logger.debug("ALERT_PERIOD: {}", ALERT_PERIOD)
    sender.add_periodic_task(ALERT_PERIOD, check_and_alert.s(), name="check-and-alert")
    sender.add_periodic_task(
        UPDATE_CL_PERIOD, update_cl_stat.s(), name="update-cl-stat"
    )


@app.task
def check_and_alert():
    flask_proc = subprocess.Popen(["flask", "check-and-alert"])
    flask_proc.communicate()


@app.task
def update_cl_stat():
    flask_proc = subprocess.Popen(["flask", "update-cl-stat"])
    flask_proc.communicate()


# @app.task
# def do_backup():
#     all_backups = [f for f in os.listdir(BACKUP_DIR) if (Path(BACKUP_DIR) / f).is_file()]
#     all_timestamps = []

#     for backup in all_backups:
#         backup_timestamp = backup.split(BACKUP_FILENAME_POSTFIX)[0]
#         try:
#             backup_timestamp = float(backup_timestamp)
#             all_timestamps.append(backup_timestamp)
#         except ValueError:
#             continue

#     make_backup(time.time())
#     all_timestamps.sort()
#     timestamps_to_delete_count = len(all_timestamps) - BACKUP_MAX_COUNT + 1
#     timestamps_to_delete_count = 0 if timestamps_to_delete_count < 0 else timestamps_to_delete_count
#     for i in range(timestamps_to_delete_count):
#         os.remove(f"{BACKUP_DIR}/{all_timestamps[i]}{BACKUP_FILENAME_POSTFIX}")
