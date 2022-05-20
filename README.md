# Tasmota-testbed

An example of a script that listens for MQTT messages sent to an MQTT-server from a Tasmota-based power sensor. The configuration is simply found in `tasmota_configuration.py`. Some basic code for setting up the [GMQTT](https://github.com/wialon/gmqtt) library, receiving the tasmota messages and an example of how they may be gathered as part of experimental data is found in `tasmota_listen.py`. Running this script once it is setup should be as simple as `python3 tasmota_listen.py`. 

* [Tasmota](https://tasmota.github.io/docs/)
* [MQTT](https://mqtt.org/)
* [Mosquitto](https://mosquitto.org/) is an MQTT server and client suite (raspbian/debian packages: `mosquitto` and `mosquitto-clients`).
  - `mosquitto_sub` is useful for debugging (e.g. see [this article](https://randomnerdtutorials.com/testing-mosquitto-broker-and-client-on-raspbbery-pi/) or [this article](http://www.steves-internet-guide.com/mosquitto_pub-sub-clients/))

## Notes on setting up the Tasmota-based power sensor and the network

The Tasmota-based power sensors we used were designed to connect to a specific pre-shared-key Wi-Fi network. You will have to check the instructions for your particular sensors. They can probably have their firmware flashed to change the Wi-Fi settings. The remaining configuration is done using HTTP over Wi-Fi.

We set up a simple pre-shared-key Wi-Fi network in our lab so that all of the Tasmota-based sensors could easily connect to it. Then we figured out which sensor corresponded to which IP address by looking at the Wi-Fi gateway's table of connected devices.

We plugged a Wi-Fi USB adapter into the server running the data-gathering script and also configured it to connect to the simple pre-shared-key Wi-Fi network.

The Tasmota-based power sensors can be configured over HTTP to send MQTT messages to a given server and port. Therefore we configured the Mosquitto server to listen to an IP-address and port combo on the Wi-Fi USB adapter's interface.

As it happens, our experimental sensor (not Tasmota) was configured to run on a different network altogether. Therefore, to avoid any issues with firewalls or network interfaces, we ran an SSH tunnel from our server to our experimental sensor, configured to forward a port from the experimental sensor to the Mosquitto server.

* e.g. `ssh -R 1800:192.168.x.y:1883 username@experimental_sensor_hostname` where
  - `1800` was chosen for the forwarded port (on the experimental sensor) but you could configure this to anything
  - `192.168.x.y` is the IP address of the Wi-Fi USB adapter running the Mosquitto server
  - `1883` is the default port of MQTT but you could configure this to anything
  - `username@experimental_sensor_hostname` are stand-ins for the username and hostname of the experimental sensor (for SSH purposes)



