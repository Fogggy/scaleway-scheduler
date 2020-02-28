import os
import json
import logging
import pytz
from datetime import datetime
from scaleway.apis import ComputeAPI
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(format='%(asctime)s> %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.DEBUG)

AUTH_TOKEN = os.getenv("AUTH_TOKEN")
SCHEDULE_FILE = os.getenv("SCHEDULE_FILE")  # path to schedule file,  for instance: ./schedule_file.json

if not AUTH_TOKEN:
    raise ValueError("AUTH_TOKEN not found.")

if not SCHEDULE_FILE:
    raise ValueError("SCHEDULE_FILE not found.")

api = ComputeAPI(auth_token=AUTH_TOKEN)
servers = api.query().servers.get()

datetime_format = "%Y-%m-%d %H:%M %z"

# Read schedule file
with open(SCHEDULE_FILE) as json_file:
    for instance in json.load(json_file):
        logging.info(f"\n")
        logging.info(f"{instance['instance_name'].upper()}")
        logging.info('-' * 50)

        # check is the instance exists in list of servers
        instance_id = None
        for server in servers['servers']:
            if server['name'] == instance['instance_name']:
                instance_id = server['id']
                instance_state = server['state']
                instance_is_running = instance_state == 'running'

        if not instance_id:
            logging.warning(f"Instance '{instance['instance_name']}' not exists.")
        else:
            logging.info(f"{instance_id}: {instance_state}")
            now = datetime.now(pytz.timezone(instance['working_hours_time_zone']))
            now_tz = now.strftime("%z")
            now_date = now.strftime('%Y-%m-%d')
            now_time = now.strftime('%H:%M')

            working_start_time = datetime.strptime(f"{now_date} {instance['working_hours'][0]} {now_tz}", datetime_format)
            working_stop_time = datetime.strptime(f"{now_date} {instance['working_hours'][1]} {now_tz}", datetime_format)

            logging.info(f"Now: {now.strftime(datetime_format)}")
            logging.info(f"Working from: {working_start_time}")
            logging.info(f"Working to: {working_stop_time}")

            if working_start_time < now < working_stop_time:
                logging.info(f"Instance {instance['instance_name']} must be turned ON")
                if not instance_is_running:
                    r = api.query().servers(instance_id).action().post({"action": 'poweron'})
                    logging.info(r)

            else:
                logging.info(f"Instance {instance['instance_name']} must be turned OFF")
                if instance_is_running:
                    r = api.query().servers(instance_id).action().post({"action": 'poweroff'})
                    logging.info(r)




