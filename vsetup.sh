#!/bin/bash

activate_path="./venv/bin/activate"

if [[ ! -f "${activate_path}" ]]; then
  echo "./venv/bin/activate not found."
  exit 1
fi

pattern=""
pattern+="deactivate () {\n"
pattern+="    # reset old environment variables"

replace=""
replace+="deactivate () {\n"
replace+="    unset DATABASE_URL\n"
replace+="    if [ -n \"\${_OLD_PYTHONPATH:-}\" ] ; then\n"
replace+="        PYTHONPATH=\"\${_OLD_PYTHONPATH:-}\"\n"
replace+="        export PYTHONPATH\n"
replace+="        unset _OLD_PYTHONPATH\n"
replace+="    fi\n"

sed -i -z "s@${pattern}@${replace}@" "${activate_path}"

pattern=""
pattern+="# unset irrelevant variables\n"
pattern+="deactivate nondestructive"

replace=""
replace+="deactivate nondestructive\n"
replace+="\n"
replace+="_OLD_PYTHONPATH=\"\$PYTHONPATH\"\n"
replace+="PYTHONPATH=\"\$VIRTUAL_ENV/lib/python3.10/site-packages\"\n"
replace+="export PYTHONPATH\n"
replace+="\n"
replace+="DATABASE_URL=\"\"\n"
replace+="export DATABASE_URL"

sed -i -z "s@${pattern}@${replace}@" "${activate_path}"
