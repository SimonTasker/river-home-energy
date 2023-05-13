# Notes

Majority of the process has been adapted from [here](https://lucassardois.medium.com/handling-iot-data-with-mqtt-telegraf-influxdb-and-grafana-5a431480217).

## Docker Network 
---

A singular `iot` network is being used across all the services.

## Mosquitto
---

Our MQTT Message broker

Can be installed and run directly as a service on the Pi, however integrates nicer with our other elements if we containerise.

The container:
```bash
> docker pull eclipse-mosquitto
```

There are two ports that mosquitto communicates over. `1883` and `9001`, which will need to be forwarded to host.

```
-p 1883:1883
-p 9001:9001
```

Mosquitto looks for `*.conf` files within `/mosquitto/config`, and so we can mount a local directory to that path in order to inject a configuration.

```
-v ./mosquitto_config:/mosquitto/config
```

Specifically, for our config, we only need to set two values

```
listener 1883
allow_anonymous true
```

This just tells the broker to listen on port 1883 for MQTT traffic and allow anonymous access (i.e. no authentication required). This will help with simpler configuration for debugging of other MQTT elements.

## InfluxDB
---

Influx is an open source time-series database that suits the needs of storing IOT-based data, due the intrinsic time-based nature at which that data is produced.

As with mosquitto it can be run directly as a service on the Pi, however we'll be containerising for simplicity.

```bash
# Specifically using latest version v2.7.1
> docker pull influxdb:2.7.1
```

The main port influx exposes is `8086`.

```
-p 8086:8086
```

There are 2 main folders used by influx for data and configuration, with an additional docker folder fo start-up scripts:
- `/etc/influxdb2` (Config)
- `/var/lib/influxdb2` (Data)
- `/docker-entrypoint-initdb.d` (Scripts)

We will be using docker volumes for influx, in order to persist data. However we will specifically mount our scripts separately, as these are really only used on first-startup.

We shall create two separate docker volumes `influxdb-config` and `influxdb-data` (within the compose file, mentioned later), and mount a local scripts folder:

```bash
-v influxdb-config:/etc/influxdb2
-v influxdb-data:/var/lib/influxdb2
-v ./influx_scripts:/docker-entrypoint-initdb.d
```

Influx uses environment variables on start up to initialise the database, which we have set to the following (within a `.env` file)

```bash
# If influx can't find existing data, this tells influx that we're doing a new setup (the alternative is 'upgrade')
DOCKER_INFLUXDB_INIT_MODE=setup
# Set a simple default user and password
DOCKER_INFLUXDB_INIT_USERNAME=admin
DOCKER_INFLUXDB_INIT_PASSWORD=adminadmin
# Configure the default org and bucket
DOCKER_INFLUXDB_INIT_ORG=HomeEnergy
DOCKER_INFLUXDB_INIT_BUCKET=main
# Specify a token (this doesn't have to be done, but it makes life easier later with telegraf)
DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=MyAwesomeAdminToken
```

There are also some common env variables used by influx, when it's running (regardless of new set-up or not), which are typically used by the influx CLI to set defaults or authentication etc.
We have defined these in another `.env` file, as they are also used by telegraf (mentioned later). We need to set these here, as our setup script uses the influx CLI, these having these set simplifies the authentication.

```bash
# Used by Influx CLI to set the default org
# Used by Telegraf conf to set the org
INFLUX_ORG=HomeEnergy
# Used by the Influx CLI and telegraf to authenticate
INFLUX_TOKEN=MyAwesomeAdminToken
# Used by the Influx CLI to define endpoint
INFLUX_HOST=http://localhost:8086
# Used by the setup script to create the additional bucket
# Used by telegraf conf to set destination bucket
INFLUX_BUCKET=MQTT_Bucket
```

Finally, we have a setup script, that is run on first-time setup of influxdb. This specifically just creates a new bucket for our telegraf instance to write to.

```bash
#!/bin/bash -x
set -e

influx bucket create \
  -n ${INFLUX_BUCKET} \
  -d "Raw data bucket for MQTT data"
```

> N.B. This script file MUST be executable, other influx cannot run it.
> ```bash
> > sudo chmod +x <script_file>
> ```

## Telegraf
---

Telegraf is an InfluxDB agent, used for collecting data and storing it within Influx.

We are using Telegraf here specifically to capture MQTT topics from our Tasmota devices.

```bash
> docker pull telegraf
```

The following command grabs an empty configuration file by running the telegraf container, that we can then use as boilerplate for our config:

```
> docker run --rm telegraf telegraf config > telegraf.conf
```

Change/add the following lines:

```conf
[[outputs.influxdb_v2]]
    # N.B. we will be using docker networks, and 'influxdb' is the hostname of the container
    urls = ["http://influxdb:8086"]

    # Token for authentication - drawn from the environment variables
    token = "$INFLUX_TOKEN"

    # Organization to write to - drawn from the environment variables
    organization = "$INFLUX_ORG"

    # Destination bucket to write into - drawn from the environment variables
    bucket = "$INFLUX_BUCKET"

[[inputs.mqtt_consumer]]
    # N.B. 'mosquitto' is the hostname of the mosquitto broker container
    servers = ["tcp://mosquitto:1883"]

    # Tasmota topics that will be subscribed to.
    topics = [
        "tele/Tasmota_Kettle/SENSOR",
        "tele/Tasmota_TV/SENSOR",
        "tele/Tasmota_Coffee/SENSOR",
    ]

    # The topics are formatted as json
    data_format = "json"
```

## Grafana
---

Grafana is a metrics query and visualisation tool, which can be hooked into InfluxDB.

```bash
> docker pull grafana/grafana
```

The main port grafana exposes is `3000`.

```
-p 3000:3000
```

There is 1 main folder used by grafana for data:
- `/var/lib/grafana`

We will be using docker volumes for grafana, in order to persist data. The volume will be `grafana-data`:

```bash
-v grafana-data:/var/lib/grafana
```

> N.B. Currently no further configuration to grafana has been set up
