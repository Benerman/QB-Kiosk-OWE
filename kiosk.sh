#! /usr/bin/bash
cd /home/studio/dashboard
source venv/bin/activate
flask --app kiosk --debug run
