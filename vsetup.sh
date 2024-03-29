#!/bin/bash

activate_path="./venv/bin/activate"

if [[ ! -f "${activate_path}" ]]; then
  echo "./venv/bin/activate not found."
  exit 1
fi

pattern="deactivate () {"

replace=""
replace+="deactivate () {  # vsetup\n"
replace+="    alias initialize=''\n"
replace+="    alias connect=''\n"
replace+="    unalias initialize\n"
replace+="    unalias connect\n"
replace+="    unset DATABASE_URL\n"
replace+="    unset TWILIO_ACCOUNT_SID\n"
replace+="    unset TWILIO_AUTH_TOKEN\n"
replace+="    unset TWILIO_SMS_NUMBER\n"
replace+="    if [ -n \"\${_OLD_PYTHONPATH:-}\" ] ; then\n"
replace+="        PYTHONPATH=\"\${_OLD_PYTHONPATH:-}\"\n"
replace+="        export PYTHONPATH\n"
replace+="        unset _OLD_PYTHONPATH\n"
replace+="    fi\n"

sed "s@^${pattern}\$@${replace}@" "${activate_path}" > temp && mv temp "${activate_path}"

pattern="export VIRTUAL_ENV"

replace=""
replace+="export VIRTUAL_ENV  # vsetup\n"
replace+="\n"
replace+="alias initialize='python -m gymbuddies.database.initialize \&\& python -m tests.generate'\n"
replace+="alias connect='python -im tests.connect'\n"
replace+="\n"
replace+="_OLD_PYTHONPATH=\"\$PYTHONPATH\"\n"
replace+="PYTHONPATH=\"\$VIRTUAL_ENV/lib/python3.10/site-packages\"\n"
replace+="export PYTHONPATH\n"
replace+="\n"
replace+="DATABASE_URL=\"\"\n"
replace+="export DATABASE_URL\n"
replace+="\n"
replace+="TWILIO_ACCOUNT_SID=\"\"\n"
replace+="export TWILIO_ACCOUNT_SID\n"
replace+="\n"
replace+="TWILIO_AUTH_TOKEN=\"\"\n"
replace+="export TWILIO_AUTH_TOKEN\n"
replace+="\n"
replace+="TWILIO_SMS_NUMBER=\"\"\n"
replace+="export TWILIO_SMS_NUMBER\n"

sed "s@^${pattern}\$@${replace}@" "${activate_path}" > temp && mv temp "${activate_path}"
