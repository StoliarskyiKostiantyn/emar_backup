import datetime


from app.logger import logger

from app.consts import STORAGE_PATH
from app.utils import (
    get_credentials,
    sftp_check_files_for_update_and_load,
    create_desktop_icon,
    download_file_from_pcc,
    self_update,
    send_activity,
)

from app.utils.send_activity import offset_to_est
from app.utils.sftp_check_files_for_update_and_load import (
    AppError,
    update_download_status,
)


def server_connect():
    logger.info("Downloading process started.")
    credentials, old_credentials = get_credentials()
    if not credentials:
        raise ValueError("Credentials not supplied. Can't continue.")

    if credentials["status"] == "success":
        # Handle errors in files downloading and zip
        try:
            if not credentials.get("use_pcc_backup"):
                last_download_time = sftp_check_files_for_update_and_load(credentials)
            else:
                download_file_from_pcc(credentials)
                last_download_time = offset_to_est(datetime.datetime.utcnow())
            send_activity(last_download_time, credentials)
            logger.info("Downloading proccess finished.")
        except (AppError, FileNotFoundError):
            update_download_status("error", credentials)
            logger.info("Downloading process interrupted")

        # user = getpass.getuser()

        create_desktop_icon()

        self_update(STORAGE_PATH, credentials, old_credentials)

    elif credentials["status"] == "registered":
        logger.info("New computer registered. Download will start next time if credentials available in DB.")

        create_desktop_icon()

    else:
        logger.info(f"SFTP credentials were not supplied. Download impossible. Credentials: {credentials}")
    logger.info("Task finished")
