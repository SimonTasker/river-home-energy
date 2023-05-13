import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = os.environ.get("INFLUXDB_TOKEN")
org = "HomeEnergy"
url = "raspberrypi.local:8086"

write_client = InfluxDBClient(url=url, token=token, org=org)

bucket="test"

write_api = write_client.write_api(write_options=SYNCHRONOUS)

for value in range(5):
    point = (
        Point("Test")
        .field("y_true", value)
        .field("y_pred", value+1)
    )
    print("Writing")
    write_api.write(bucket=bucket, org=org, record=point)
    time.sleep(5)

# query_api = write_client.query_api()

# query = """from(bucket: "test")
#  |> range(start: -1m)"""
# tables = query_api.query(query, org=org)

# print("TABLES")

# for table in tables:
#   for record in table.records:
#     print(record)