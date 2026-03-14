FROM node:alpine

WORKDIR /usr/app

COPY ./static ./static
COPY ./voicewake ./voicewake
COPY ./frontend ./frontend
COPY ./tailwind.config.js ./tailwind.config.js

RUN npm cache clean --force
RUN npm install tailwindcss
RUN npm install @tailwindcss/cli

#behaviours
    #"start" at package.json is always run by Docker
        #is seemingly skipped to the next non-empty command if "start" has empty "" command
    #"start" is usually used to start up Node server
#context
    #we are currently only using this for Tailwind's watcher
    #we do not need any Node server
    #there seems to be a consensus against running "npm run start" as CMD here, as it can hide errors
#problem #1
    #"start" must exist in package.json, but we don't need to run anything else
    #leaving "start" empty but having Tailwind watch as script in package.json causes Docker to auto-skip and auto-run next script
#solution #1
    #let "start" be empty, and let "start" be the only script
    #don't run Tailwind via package.json script, since empty "start" will go to the next script, and you'll get "exited with code 0"
#problem #2
    #we have successful bind mount, and correct tailwind.config.js
    #however, on file change, Tailwind watch does not rebuild
#solution #2
    #add "--poll" flag to use polling instead of filesystem events
        #file system events are unreliable when propagating changes from host files to container
        #saw a comment saying that file system events don't work when Docker is running in Hyper-V
            #if you have server script, also use polling, e.g. "nodemon -L server.js"

CMD ["sh", "-c", "npx @tailwindcss/cli -i ./static/voicewake/css/base.css -o ./static/voicewake/css/output.css --watch --poll"]