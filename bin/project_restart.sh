#!/bin/bash

bin/restart_uwsgi.sh && supervisorctl restart cc-celery && supervisorctl restart cc-celerybeat
