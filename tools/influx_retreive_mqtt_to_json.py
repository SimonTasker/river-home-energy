from influxdb_client import InfluxDBClient
import os
import json
import pickle

# InfluxDB settings
influxdb_host = "raspberrypi.local"
influxdb_port = 8086
influxdb_token = os.environ['INFLUX_TOKEN']
influxdb_org = "HomeEnergy"
influxdb_bucket = "MQTT_Bucket"
topic = "tele/Tasmota_Kettle/SENSOR"
period = "-5d"
flux_query = f'from(bucket:"{influxdb_bucket}")\
    |> range(start: {period})\
    |> filter(fn: (r) => r["topic"] == "{topic}")'

# Pickle settings
output_file = "output_5d.pkl"

# Connect to InfluxDB
influxdb_client = InfluxDBClient(url=f"http://{influxdb_host}:{influxdb_port}", token=influxdb_token, org=influxdb_org)

# Query data using Flux
query_api = influxdb_client.query_api()
tables = query_api.query(query=flux_query)

output=[]

for table in tables:
    record_num = 0
    for record in table.records:

        if len(output) <= record_num:
            output.append({})
        output[record_num]["Time"] = record.get_time().strftime('%Y-%m-%dT%H:%M:%S')

        field = record.get_field().replace("ENERGY_", "")
        value = record.get_value()

        if "ENERGY" not in output[record_num]:
            output[record_num]["ENERGY"] = {}
        output[record_num]["ENERGY"][field] = value
        record_num += 1

# Pickle the JSON data
pickled_data = pickle.dumps(output)

# Save the pickled data to the file
with open(output_file, "wb") as file:
    file.write(pickled_data)

print("Pickled data saved to ", output_file)
