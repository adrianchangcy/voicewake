import subprocess
from time import sleep

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
    #to run: py django_runserver.py
    #to stop: Ctrl+C

if __name__ == '__main__':

    while True:

        try:
            #0.0.0.0 to catch all IPv4 addresses
                #as long as port matches, we can connect
            #Docker
                #Django uses StatReloader, i.e. polling, so changes at host files via bind mounts are detected
                #do not bind at 127.0.0.1:8000, since 127.0.0.1 inside container means "this container"
                #we cannot open browser from within container, so using host browser results in error
                #we bind to 0.0.0.0:8000, so at host browser, just visit 127.0.0.1:8000 or localhost:8000
            subprocess.run(
                [
                    'python',
                    'manage.py',
                    'runserver',
                    '0.0.0.0:8000',
                ],
            )
        except KeyboardInterrupt:
            break
        except:
            raise

        print('Unable to start. Trying again...')
        sleep(1)
