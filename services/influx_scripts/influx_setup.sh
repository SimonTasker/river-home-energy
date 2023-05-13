#!/bin/bash -x
set -e

influx bucket create \
  -n ${INFLUX_BUCKET} \
  -d "Raw data bucket for MQTT data"