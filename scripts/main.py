import logging
import logging.config
import os
import sys
import time
from datetime import datetime, timedelta

import dotenv
import schedule

from const import *
from data_fetcher import DataFetcher
from mqtt_updator import MqttUpdator


def main():
    # 读取 .env 文件
    dotenv.load_dotenv(verbose=True)
    global RETRY_TIMES_LIMIT
    try:
        PHONE_NUMBER = os.getenv("PHONE_NUMBER")
        PASSWORD = os.getenv("PASSWORD")
        MQTT_HOST = os.getenv("MQTT_HOST")
        MQTT_PORT = int(os.getenv("MQTT_PORT"))
        MQTT_USER = os.getenv("MQTT_USER")
        MQTT_PASS = os.getenv("MQTT_PASS")
        JOB_START_TIME = os.getenv("JOB_START_TIME")
        LOG_LEVEL = os.getenv("LOG_LEVEL")
        VERSION = os.getenv("VERSION", 'null')

        RETRY_TIMES_LIMIT = int(os.getenv("RETRY_TIMES_LIMIT", 5))
    except Exception as e:
        logging.error(f"Failing to read the .env file, the program will exit with an error message: {e}.")
        sys.exit()

    logger_init(LOG_LEVEL)
    logging.info(f"The current repository version is {VERSION}")

    fetcher = DataFetcher(PHONE_NUMBER, PASSWORD)
    updator = MqttUpdator(MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS)
    logging.info(f"The current logged-in user name is {PHONE_NUMBER}, the mqtt address is {
                 MQTT_HOST}, and the program will be executed every day at {JOB_START_TIME}.")

    next_run_time = datetime.strptime(JOB_START_TIME, "%H:%M") + timedelta(hours=12)
    logging.info(f'Run job now! The next run will be at {JOB_START_TIME} and {
                 next_run_time.strftime("%H:%M")} every day')
    schedule.every().day.at(JOB_START_TIME).do(run_task, fetcher, updator)
    schedule.every().day.at(next_run_time.strftime("%H:%M")).do(run_task, fetcher, updator)
    run_task(fetcher, updator)

    while True:
        schedule.run_pending()
        time.sleep(1)


def run_task(data_fetcher: DataFetcher, mqtt_updator: MqttUpdator):
    for retry_times in range(1, RETRY_TIMES_LIMIT + 1):
        try:
            user_id_list, balance_list, last_daily_date_list, last_daily_usage_list, yearly_charge_list, yearly_usage_list, month_list, month_usage_list, month_charge_list = data_fetcher.fetch()
            # user_id_list, balance_list, last_daily_date_list, last_daily_usage_list, yearly_charge_list, yearly_usage_list, month_list, month_usage_list, month_charge_list = ['123456'],[58.1],['2024-05-12'],[3.0],['239.1'],['533'],['2024-04-01-2024-04-30'],['118'],['52.93']
            for i in range(0, len(user_id_list)):
                # balance_lis[i] 余额
                # last_daily_usage_list[i] 当日用量
                # last_daily_date_list[i] 当日日期
                # month_charge_list[i] 上月电费
                # month_usage_list[i] 上月用量
                # yearly_charge_list[i] 当年电费
                # yearly_usage_list[i] 当年用量
                mqtt_updator.update(user_id_list[i], balance_list[i], last_daily_usage_list[i], last_daily_date_list[i], month_charge_list[i],
                                    month_usage_list[i], yearly_charge_list[i], yearly_usage_list[i])
            logging.info("state-refresh task run successfully!")
            return
        except Exception as e:
            logging.error(f"state-refresh task failed, reason is [{e}], {RETRY_TIMES_LIMIT - retry_times} retry times left.")
            continue

def logger_init(level: str):
    logger = logging.getLogger()
    logger.setLevel(level)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    format = logging.Formatter("%(asctime)s  [%(levelname)-8s] ---- %(message)s", "%Y-%m-%d %H:%M:%S")
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setFormatter(format)
    logger.addHandler(sh)


if __name__ == "__main__":
    main()
