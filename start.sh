#!/usr/bin/env bash

configfile=/usr/src/app/config/AnovaMaster.cfg

if [ ! -f $configfile ]; then
	  cp /usr/src/app/AnovaMaster.cfg.sample $configfile
  fi

python run.py

