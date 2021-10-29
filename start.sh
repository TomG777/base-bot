#!/usr/bin/env bash
run=true
#variables for easy updating of the autostart script
#Python command
if ! command -v python3.9 &> /dev/null
then
    if ! command -v python3.8 &> /dev/null
    then
        if ! command -v python3.7 &> /dev/null
        then
            echo "Using Python3"
            PY="python3"
        else
            echo "Using Python3.7"
            PY="python3.7"
        fi
    else
        echo "Using Python3.8"
        PY="python3.8"
    fi
else
    echo "Using Python3.9"
    PY="python3.9"
fi

PY="python3.8"
#Base file
BASE="base.py"
#Run command
COMMAND="$PY $BASE # morningbot"
#Restart parameter file
RSFILE="data/restart.txt"
#Stop parameter
STOP="stop"
#Run parameter
RUN="run"

#Script
#Set $RUN in restart file
echo $RUN > $RSFILE
echo "Starting bot for first time at: $(date)"
#Run the bot
eval "$COMMAND"
#Infinite while true loop
while :
do
    echo "Running check again at: $(date)"
    if [ "$run" = false ]
    then
        echo "stopping because of run variable being false"
        break
    fi
    if grep -q $STOP $RSFILE
    then
        echo "stopping because of stop in file"
        run=false
        break
    fi
    if grep -q $RUN $RSFILE
    then
        # shellcheck disable=SC2162
        read -t 5 -p "Reloading bot in a bit or on user input!"
        echo "Reloading now! at: $(date)"
        eval "$COMMAND"
    fi
done
echo "Exiting at: $(date)"
exit
