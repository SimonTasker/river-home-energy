FROM simontasker/docker-river-home-energy

WORKDIR ~

COPY . .

RUN python home_energy.py

