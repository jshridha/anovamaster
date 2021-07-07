#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import datetime
import sys

sys.stdout.write('%s Copying Config Details ...\n' % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

ANOVA_MAC = os.getenv('ANOVA_MAC', '')
MQTT_USERNAME = os.getenv('MQTT_USERNAME', '')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', '')
MQTT_HOST = os.getenv('MQTT_HOST', '127.0.0.1')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TIMEOUT = int(os.getenv('MQTT_TIMEOUT', 60))
MQTT_PREFIX = os.getenv('MQTT_PREFIX', 'anova')
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')

f = open("/usr/src/Anova/config/AnovaMaster.cfg", "w")

f.write("[main]\n")
f.write("log_file = anovamaster.log\n")
f.write("log_level = %s\n" % LOGGING_LEVEL)
f.write("\n")
f.write("[anova]\n")
f.write("mac = %s\n" % ANOVA_MAC)
f.write("\n")
f.write("[mqtt]\n")
f.write("server = %s\n" % MQTT_HOST)
f.write("username = %s\n" % MQTT_USERNAME)
f.write("password = %s\n" % MQTT_PASSWORD)
f.write("port = %s\n" % MQTT_PORT)
f.write("status_topic = %s" % MQTT_PREFIX + "/status\n")
f.write("status_timer = %s" % MQTT_PREFIX + "/timer\n")
f.write("run_command_topic = %s" % MQTT_PREFIX + "/command/run\n")
f.write("timer_run_command_topic = %s" % MQTT_PREFIX + "/command/timer_run\n")
f.write("temp_command_topic = %s" % MQTT_PREFIX + "/command/temp\n")
f.write("timer_command_topic = %s" % MQTT_PREFIX + "/command/timer\n")

f.close()