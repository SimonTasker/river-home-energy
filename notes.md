# Setting up Raspberry Pi

## OS Installation

> TODO

## Mount USB Storage Drive

> TODO

# Setting up Docker

## Installation

```bash
# Ensure Pi is up-to-date
$ sudo apt update
$ sudo apt upgrade
# Run Docker install script
$ curl -sSL https://get.docker.com | sh
# Modify permissions (replace <pi-user> with main user)
$ sudo usermode -aG docker <pi-user>
# Reboot system
$ sudo reboot

# Check docker works correctly
$ docker -v
```

## Change Docker's Storage Directory

By default docker uses the `/var/lib/docker` directory as it's main storage directory for images etc.\
This directory is part of the root filesystem of the Raspberry Pi, and so if the SD card used to install the OS on is quite small (e.g. 32GB) then the downloading and usage of docker images can saturate this drive quite quickly.

As an alternative, we can bind mount this directory to a directory located on a mass storage device (see [Mount USB Storage Drive](#mount-usb-storage-drive)).

To this, follow:

```bash
# Remove all running containers and all stored images
$ docker rm -f $(docker ps -aq)
$ docker rmi -f $(docker images -q)
# Stop the running docker service
$ sudo systemctl stop docker
# Remove and re-create the /var/lib/docker directory
$ sudo rm -rf /var/lib/docker
$ sudo mkdir /var/lib/docker
# Create the target folder to bind mount to
$ sudo mkdir /mnt/data/docker
# Create the mount
$ sudo mount --rbind /mnt/data/docker /var/lib/docker
```

To make this permanent, we must also update `fstab`

```bash
$ sudo vim /etc/fstab

# Add the following to the end of the file - and save
/mnt/data/docker /var/lib/docker none rbind 0 0
```

Then restart the docker service
```bash
$ sudo systemctl start docker
```

# Setting up Tasmota Devices

## Configuring MQTT

---
### Setting up MQTT host on Raspberry Pi
---

Install the Mosquitto Broker

```bash
$ sudo update install mosquitto
# Check installation
$ mosquitto -v
# Enable service to start on boot
$ sudo systemctl enable mosquitto.service
# Check service is running
$ sudo service mosquitto status
```

Update the Mosquitto configuration to allow for anonymous access (simply as convenience for testing)

```bash
$ sudo vim /etc/mosquitto/mosquitto.conf

# Ensure these two lines are set to
listener 1883
allow_anonymous true

# Then restart the service
$ sudo systemctl restart mosquitto
```

---
### Update Tasmota MQTT Configuration
---

Within the Tasmota Web Interface, navigate to:

> Configuration > Configure MQTT

Simply update the Host parameter to `raspberrypi.local` and Port to `1883`

To ensure we also get more frequent updates from the device, within the Web Console

```bash
# The number after TelePeriod is the number of seconds between each update, in this case, every 10 s
TelePeriod 10
```

## Configuring NTP

---
### Setting up Raspberry Pi as NTP Server
---

Install NTP Server

```bash
$ sudo update install ntp
# Check installation
$ sntp --version
sntp 4.2.8p15@1.3728-o Wed Sep 23 11:46:38 UTC 2020 (1)
# Enable service to start on boot
$ sudo systemctl enable ntp.service
# Check service is running
$ sudo service ntp status
```

---
### Update Tasmota devices to use Raspberry Pi as NTP Server
---

Within the Tasmota Web Console we first need to point to the new NTP server

```bash
# Updates the first checked NTPSERVER address to the raspberry pi
NTPSERVER1 raspberrypi.local
# At any time, this can be reset to firmware defaults with
NTPSERVER1 1
```

Also ensure that the device has the correct timezone settings, as defined by https://tasmota.github.io/docs/Timezone-Table/

```bash
# Timezone for Europe/London
Backlog0 Timezone 99; TimeStd 0,0,10,1,2,0; TimeDst 0,0,3,1,1,60
# Backlog0 allows chaining of commands
```

Restart the device for changes to take affect

```bash
Restart 1
```

# Using River within Docker

## Building the Container

For both building processes, the dockerfile is the same:

```
# Using python3.9 as base image
FROM python:3.9-slim-buster

WORKDIR /

# Install required libraries and packages
RUN apt update && apt install -y \
    build-essential \
    libtool \
    autoconf \
    unzip \
    curl \
    wget \
    libssl-dev \
    gfortran \
    pkg-config \
    libopenblas-dev

# Available debian package for cmake not high enough version
# Download and install newer version (3.25.0)
RUN mkdir ~/temp && cd ~/temp \
    && wget https://cmake.org/files/v3.25/cmake-3.25.0.tar.gz \
    && tar -zxf cmake-3.25.0.tar.gz \
    && cd cmake-3.25.0 \
    && ./bootstrap \
    && make \
    && make install
# Remove temp directory after cmake install
RUN cd ~ && rm -rf temp/
# Preinstall all the required python libraries that river uses.
# The river install process is slightly more graceful if we do this first
RUN pip install numpy
RUN pip install pandas
RUN pip install scipy
# Need to mount .cargo folder as tmpfs in order to get around large file issue on arm/v7 images
# https://github.com/rust-lang/cargo/issues/8719
RUN --mount=type=tmpfs,target=/root/.cargo curl -sSf https://sh.rustup.rs | bash -s -- -y \
    && export PATH="/root/.cargo/bin:${PATH}" \
    && pip install river
RUN pip install paho-mqtt
RUN pip install grpcio
```
---
### Using the Raspberry Pi
---

> This build process has been tested on the Raspberry Pi 4 with 2GB RAM, with standard Raspian OS installed on a 32GB SD card.

Because of the limited available memory, and small default swap file size (100MB), we need to increase the swap file size in order to accomodate the docker build process.

> N.B. Unlikely to be an issue with the 4GB or 8GB RAM variants

To increase the swap file size, we must first tell the raspberry pi to stop using the current swap file:
```bash
$ sudo dphys-swapfile swapoff
```
Now we can update swap configuration:
```bash
$ sudo vim /etc/dphys-swapfile

# Within the file, change this:
   CONF_SWAPSIZE=100
# to this:
   CONF_SWAPSIZE=1024
```
In doing this, we are increase the swap file size from 100MB to 1GB.\
Next we have to configure swap file:
```bash
$ sudo dphys-swapfile setup
```
And then we can turn the swap file back on, and reboot for the changes to take effect.
```bash
$ sudo dphys-swapfile swapon
$ sudo reboot
```

Now that we have sufficient Memory capacity on the Pi, we can build the container:
```bash
$ docker build --tag river-raspberrypi .
```

---
### Cross-compiling
---

To cross compile, we need to use `buildx`, an extension to `docker build`.

`buildx` comes installed as standard with Docker Desktop for Windows and MacOS.

`buildx` allows the user the define builder instances, which define what targets to build to. For example, the default builder provides a few standard build targets:

```
$ docker buildx ls
NAME/NODE       DRIVER/ENDPOINT             STATUS  BUILDKIT PLATFORMS
default         docker                                       
  default *     default                     running 20.10.21 linux/amd64, linux/arm64, linux/riscv64, linux/ppc64le, linux/s390x, linux/386, linux/arm/v7, linux/arm/v6
```
Specifically, it includes `linux/arm/v7` which is the same architecture as the Raspberry Pi.
> You can check the Raspberry Pi's architecture by running the following on the device:
> ```bash
> $ uname -m
> ```
Because the default builder has the correct target architecture, we don't need to define our own.\
Instead, we can jump straight to building:

```bash
$ docker buildx build --platform linux/arm/v7 -t river-raspberrypi .
```
Note that we include the target platform choice. If this is excluded, docker will build for all the target platforms within the builder's architecture list. This will then take a while...

## Using the container
---
```bash
$ docker run -d \
    --name river-test-1 \
    --privileged \
    -v /mnt/data:/data \
    --network=host \
    river-raspberrypi
```

If you don't immediately start a process in the container, it was just exit even in detatched mode.

Add the following to the end of the command to run a null process, and allow the container to stay alive.

```bash
> docker run -d \
    --name river-test-1 \
    --privileged \
    -v /mnt/data:/data \
    --network=host \
    river-raspberrypi \
    tail -f /dev/null
```
To interact with the container:

```bash
> docker exec -it river-test-1 /bin/bash
```
This opens an interactive session with the running container and runs the bash terminal.

# Setting up Home Assistant

```bash
docker run -d \
  --name homeassistant \
  --privileged \
  --restart=unless-stopped \
  -e TZ=Europe/London \
  -v /mnt/data/homeassistant_config:/config \
  --network=host \
  ghcr.io/home-assistant/home-assistant:stable
```