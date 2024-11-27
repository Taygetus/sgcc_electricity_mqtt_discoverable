import os
import logging
from datetime import datetime
from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import Sensor, SensorInfo

from const import *


class MqttUpdator:
    def __init__(self, mqtt_host: str, mqtt_port: int, mqtt_user: str, mqtt_pass: str):
        self.mqtt_settings = Settings.MQTT(host=mqtt_host, port=mqtt_port, username=mqtt_user, password=mqtt_pass)
        self.date_icon = 'mdi:calendar-range'  # 图标：日期
        self.cost_icon = 'mdi:currency-cny'  # 图标：人民币
        self.use_icon = 'mdi:lightning-bolt-outline'  # 图标：电

    def __set_state(self, device_info, name, unique_id, state, icon, unit_of_measurement=None,):
        sensor_info = SensorInfo(name=name, unique_id=unique_id, object_id=unique_id,
                                 unit_of_measurement=unit_of_measurement,
                                 device=device_info, icon=icon)
        settings = Settings(mqtt=self.mqtt_settings, entity=sensor_info)
        sensor = Sensor(settings)
        sensor.set_state(state)

    def update(self, user_id: str, balance_list: float, last_daily_usage: float, last_daily_date: str, month_charge: str, month_usage: str, yearly_charge: str, yearly_usage: str):
        device_name = f'电-{user_id}'
        device_info = DeviceInfo(name=device_name, identifiers=f'electricity_{user_id}',
                                 manufacturer='taygetus', model=f'electricity_{user_id}')

        # 余额
        self.__set_state(device_info, 'balance', f'balance_{user_id}', balance_list, self.cost_icon, BALANCE_UNIT)

        # 当日用量
        self.__set_state(device_info, 'day', f'day_{user_id}', last_daily_date, self.date_icon)
        self.__set_state(device_info, 'day_use', f'day_use_{user_id}', last_daily_usage, self.use_icon, USAGE_UNIT)

        # 上月电费
        self.__set_state(device_info, 'last_month_cost', f'last_month_cost_{user_id}', month_charge, self.cost_icon, BALANCE_UNIT)

        # 上月用量
        self.__set_state(device_info, 'last_month_use', f'last_month_use_{user_id}', month_usage, self.use_icon, USAGE_UNIT)

        # 当年电费
        self.__set_state(device_info, 'this_year_cost', f'this_year_cost_{user_id}', yearly_charge, self.cost_icon, BALANCE_UNIT)

        # 当年用量
        self.__set_state(device_info, 'this_year_use', f'this_year_use_{user_id}', yearly_usage, self.use_icon, USAGE_UNIT)

        logging.info(f"updated device:{device_name}")
