# AnovaMaster

AnovaMaster acts as a bridge between an Anova immersion sous vide device
and an MQTT bus. It broadcasts current status of the cooker on a given
MQTT channel, and receives commands to control the device.

It was written to integrate with [Home Assistant](https://home-assistant.io/)
using the [MQTT HVAC](https://home-assistant.io/components/climate.mqtt/)
component. But should work well with any other automation system.

## Requirements

* Any Bluetooth adapter supported by Linux should work. I've only ever tested
this running on a Raspberry Pi Zero W, though.
* Python 2. Sorry.

## Installation

* Check out the code and change in to the new directory.
* Install dependencies

        $ sudo apt-get install libglib2.0-dev virtualenv

* Create and activate a python virtual environment

        $ virtualenv venv
		$ . venv/bin/activate

* Install dependencies

		$ pip install -r requirements.txt
		
* Create a configuration file. Refer to comments in the config file for
  how to set it up.

		$ cp config/AnovaMaster.cfg.sample config/AnovaMaster.cfg
		$ nano config/AnovaMaster.cfg
		
* Run it.

		$ ./run.py

## Status packet

AnovaMaster broadcasts regular status messages to MQTT. The payload of these
is a JSON packet with the following format:

        {
		  "state": "running",
		  "current_temp": "140",
		  "target_temp": "140",
		  "temp_unit": "F"
	    }

### state

The state field will be one of

* "stopped"
* "running"
* "disconnected"

### Temperatures

Temperatures are represented as a string, accurate to one decimal place. The
`temp_unit` field will be one of

* "C"
* "F"

## Sending commands

AnovaMaster currently supports turning the Anova on/off, and setting the
temperature. Each can be done by sending a message with the topic as
configured in the config file.

### Setting state

The payload should be one of these strings

* "stopped" - turn the Anova off
* "running" - turn the Anova on

### Setting temperature

The payload should be a float. AnovaMaster will set it as the desired
temperature in whichever unit the Anova is currently set to. The
temperature must be inside these limits, otherwise it will be discarded:

|         | Celsius | Fahrenheit |
|---------|---------|------------|
| Maximum | 20      | 77         |
| Minimum | 99      | 210        |

## Integration with Home Assistant

I'm using the following in my `configuration.yaml` to integrate with
this script:

	climate:
      - platform: mqtt
        name: Sous vide
        modes:
          - disconnected
          - stopped
          - running
        current_temperature_topic: anova/status
        current_temperature_template: "{{ value_json.current_temp }}"
        temperature_state_topic: anova/status
        temperature_state_template: "{{ value_json.target_temp }}"
        mode_state_topic: anova/status
        mode_state_template: "{{ value_json.state }}"
        mode_command_topic: anova/command/run
        temperature_command_topic: anova/command/temp
		
```
sudo cp anova.service /lib/systemd/system/
sudo systemctl enable anova.service
sudo systemctl start anova.service
```

