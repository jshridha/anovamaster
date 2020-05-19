set -e
configfile=/usr/src/Anova/config/AnovaMaster.cfg

if [ ! -f $configfile ]; then
	python /usr/src/Anova/config/Create_Config.py
fi

cd /usr/src/Anova
hciconfig hci0 down && hciconfig hci0 up
if [ ! -f "/usr/src/Anova/venv/bin/activate" ]; then
	virtualenv venv
	. venv/bin/activate
	pip install -r requirements.txt
	python -u run.py
else
	. venv/bin/activate
	python -u run.py
fi