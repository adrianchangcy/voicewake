FROM node:current-alpine

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

#behaviours
    #"start" at package.json is always run by Docker
        #is seemingly skipped to the next non-empty command if "start" has empty "" command
    #"start" is usually used to start up Node server
#context
    #we are currently only using this for Tailwind's watcher
    #we do not need any Node server
    #there seems to be a consensus against running "npm run start" as CMD here, as it can hide errors
#solution
    #use "start" for Tailwind watcher
    #don't run CMD here, since "start" always runs by container, otherwise you get "exited with code 0"
CMD ["tailwindcss", "-i", "./static/voicewake/css/base.css", "-o", "./static/voicewake/css/output.css", "--watch"]