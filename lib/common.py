import json

def instrument_init(self, instrument, base_path):
    config_path = "%s/config" % base_path
    config_file = open("%s/instruments.config" % config_path, "r")
    jsonData = json.load(config_file)
    config_data = jsonData[instrument]
    return config_data

def account_init(self, mode, base_path):
    property_path = "%s/property" % base_path
    property_file = open("%s/account.properties" % property_path, "r")
    jsonData = json.load(property_file)
    account_data = jsonData[mode]
    return account_data
