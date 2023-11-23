import configparser

config_file = configparser.ConfigParser()

config_file["App Settings"] = {
    "Name":"Kettle Predictor"
}

config_file["MQTT Settings"] = {
    "Address":"raspberrypi.local",
    "Port":1883,
    "Topic":"tele/Tasmota_Kettle/SENSOR"
}

config_file["River Settings"] = {
    "Model File":"kettle_predictor_model.pkl"
}

config_file["InfluxDB Settings"] = {
    "Address":"http://raspberrypi.local:8086",
    "Org":"HomeEnergy",
    "Bucket":"Energy"
}

config_file["gRPC Settings"] = {
    "Address":"[::]:50051"
}

with open(r"configuration.ini", 'w') as config_file_obj:
    config_file.write(config_file_obj)
    config_file_obj.flush()
    config_file_obj.close()

print("Created 'configuration.ini'")