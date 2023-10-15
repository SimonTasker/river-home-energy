# Services

Contains docker compose definition for starting background services

Specifically:
- Mosquitto Broker
- Influx Database
- Telegraf (MQTT Listener)
- Home Assistant

All services are connected within docker network named `iot`.\
Both `InfluxDB` and `Home Assistant` are configured with docker volumes for persistent storage.\
The `mosquitto_config`, `telegraf_config` and `influx_scripts` folders are bind-mounted to each service appropriately.

## Details
---

### Mosquitto

The mosquitto service is configured as a simple, anonymous access, MQTT broker, listening on port `1883`

### InfluxDB

InfluxDB is a time-series database, which we shall use for storing data from our system.

The service has environment variables and a set-up script that are configured to auto configure the database on first set-up, with the initial values:

- Default User: `admin`
- Default Password: `adminadmin`
- Default Org: `HomeEnergy`
- Default Bucket: `main`
- Additional Bucket: `MQTT_Bucket`

If the service is restarted (without deleting the corresponding docker volumes), then all previous data will be restored.

### Telegraf

Telegraf is a data collection service for InfluxDB.
We have configured this service to explicitly connect to our MQTT service and record data about specific topics, into the InfluxDB service.

Specifically these topics are:

- `tele/Tasmota_Kettle/SENSOR`
- `tele/Tasmota_TV/SENSOR`
- `tele/Tasmota_Coffee/SENSOR`

These relate to our current Tasmota device configurations.\
(N.B. These can be modified in `./telegraf_config/mqtt_telegraf.conf`)

## Running
---

Make sure the influx_setup.sh is executable

```bash
> sudo chmod +x ./influx_scripts/influx_setup.sh
```

Then simply:

```bash
> docker compose up -d
```

The following services will be then available:

| Service        | Local Address         | Raspberry Pi Address          |
| -------------- | --------------------- | ----------------------------- |
| MQTT           | mqtt://localhost:1883 | mqtt://raspberrypi.local:1883 |
| InfluxDB       | http://localhost:8086 | http://raspberrypi.local:8086 |
| Home Assistant | http://localhost:8123 | http://raspberrypi.local:8123 |