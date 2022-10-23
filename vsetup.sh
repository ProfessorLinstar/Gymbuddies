#!/bin/bash

activate_path="./venv/bin/activate"

if [[ ! -f "${activate_path}" ]]; then
  echo "./venv/bin/activate not found."
  exit 1
fi

pattern=""
pattern+="deactivate () {"

replace=""
replace+="deactivate () {  # vsetup\n"
replace+="    unset DATABASE_URL\n"
replace+="    if [ -n \"\${_OLD_PYTHONPATH:-}\" ] ; then\n"
replace+="        PYTHONPATH=\"\${_OLD_PYTHONPATH:-}\"\n"
replace+="        export PYTHONPATH\n"
replace+="        unset _OLD_PYTHONPATH\n"
replace+="    fi\n"

sed -E "s@${pattern}@${replace}@" "${activate_path}" > temp
mv temp "${activate_path}"

pattern=""
pattern+="deactivate nondestructive"

replace=""
replace+="deactivate nondestructive  # vsetup\n"
replace+="\n"
replace+="_OLD_PYTHONPATH=\"\$PYTHONPATH\"\n"
replace+="PYTHONPATH=\"\$VIRTUAL_ENV/lib/python3.10/site-packages\"\n"
replace+="export PYTHONPATH\n"
replace+="\n"
replace+="DATABASE_URL=\"\"\n"
replace+="export DATABASE_URL"

sed -E "s@${pattern}@${replace}@" "${activate_path}" > temp
mv temp "${activate_path}"
