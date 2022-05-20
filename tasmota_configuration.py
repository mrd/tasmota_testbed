# Name/ID of Tasmota-based sensor (in its configuration)
tasmota_id = 'tasmota'

# IP address / port of MQTT server
host = '192.168.1.1'
port = 1883

# Username / password of MQTT server
user = '<username>'
pwrd = '<password>'

# Directory in which to store received data
data_dir = 'data'


# Tasmota-based power sensors have their own ID (from their configuration; see above).
# ACP_ID is what we call the unique identifier for our sensor (the one being tested).

# The tasmota_to_acp_id dictionary maps tasmota sensor identifiers to
# their associated test harness sensor. In other words, it maps the
# tasmota power sensor to the experimental sensor that is receiving
# the power.
tasmota_to_acp_id = { 'tasmota': 'my_sensor' }

# If the code is modified to allow for more than one tasmota-based
# power sensor then this above dictionary will need to have more than
# one entry.
