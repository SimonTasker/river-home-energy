#!/bin/bash -x
set -e

influx bucket create \
  -n MQTT_Bucket \
  -d "Raw data bucket for MQTT data"