from influxdb_client import InfluxDBClient
import os
import pickle

# Helper script to go extract data from the InfluxDB, and format
# it back into the equivalent Tasmota JSON format
# Pickles the data before saving

# InfluxDB settings
influxdb_host = "raspberrypi.local"
influxdb_port = 8086
influxdb_token = os.environ['INFLUX_TOKEN']
influxdb_org = "HomeEnergy"
influxdb_bucket = "MQTT_Bucket"
# Topic to query
topic = "tele/Tasmota_Kettle/SENSOR"
# Tweek depending on how much data needed
# (N.B. the further back you go, the longer this takes to run)
period = "-30d"
flux_query = f'from(bucket:"{influxdb_bucket}")\
    |> range(start: {period})\
    |> filter(fn: (r) => r["topic"] == "{topic}")'

# Pickle settings
output_file = "output_kettle_30d.pkl"

# Connect to InfluxDB
influxdb_client = InfluxDBClient(url=f"http://{influxdb_host}:{influxdb_port}", token=influxdb_token, org=influxdb_org)

# Query data using Flux
query_api = influxdb_client.query_api()
tables = query_api.query(query=flux_query)

output=[]

# Influx breaks each ENERGY data element into its own table 
# Therefore we need to merge all these tables back into individual
# records - as they would have been produced by the Tasmota SENSOR
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
