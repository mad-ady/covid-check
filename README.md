# covid-check
Check availability on https://programare.vaccinare-covid.gov.ro/

Uses Selenium to run a Chrome browser instance (selenium and chromedriver needs to be installed separately - see https://sites.google.com/a/chromium.org/chromedriver/downloads), logs into https://programare.vaccinare-covid.gov.ro/ and (currently) checks a list of patients to see if they are allowed to make a vaccination appointment. If they are, an external program is called to notify the patients (I used telegram-send, for instance).

Configuration is done in covid.yaml

Dependencies:
```
pip3 install PyYAML selenium 
```

Usage:

```
python3 covid-check.py covid.yaml
```

Should run as a cron job.
