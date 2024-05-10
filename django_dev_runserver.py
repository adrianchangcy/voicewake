import subprocess
from time import sleep
import sys

#issue
    #sometimes, Django would fail silently, and manually restarting would fail silently
    #this continues for maybe >= 0 times
    #seems to happen inconsistently/unpredictably when changing settings
    #no profilers that can show stack trace nor profile at precisely when the default command is run:
        #py manage.py runserver --settings=voicewake.settings.dev
#solution
    #call this, and this script will auto-restart infinitely on error
    #when subprocess has no error, the "while" loop is suspended
#aesthetics
    #tried sys.exit(0), subprocess.run(stderr=subprocess.DEVNULL, captue_output=False,)
    #on KeyboardInterrupt, always exits with 1 at VSCode Powershell
#instructions
    #to run: py dev_runserver.py
    #to stop: Ctrl+C

if __name__ == '__main__':

    while True:

        try:
            subprocess.run(
                [
                    'py',
                    'manage.py',
                    'runserver',
                    '0.0.0.0:8000',
                    '--settings=voicewake.settings.dev',
                ],
            )
        except KeyboardInterrupt:
            break
        except:
            raise

        print('Unable to start. Trying again...')
        sleep(1)
