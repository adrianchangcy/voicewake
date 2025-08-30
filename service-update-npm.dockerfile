FROM node:current-alpine

#tailwind

WORKDIR .

COPY ./package.json ./
COPY ./yarn.lock ./

#frontend

WORKDIR ./frontend

COPY ./frontend/package.json ./
COPY ./frontend/yarn.lock ./

WORKDIR ../

#keep container alive
CMD ["sh", "-c", "echo 'Container is running...'; sleep infinity"]


#==================================================================================
#commands part 1, in container:
    #npm install -g npm-check-updates
    #ncu
    #ncu -u
    #yarn install --dry-run --check-files
    #yarn install
    #cd frontend
    #ncu
    #ncu -u
    #yarn install --dry-run --check-files
    #yarn install

#commands part 2, at host machine project root, cmd:
    #docker cp vw_dev-update_npm-1:/package.json ./package.json
    #docker cp vw_dev-update_npm-1:/yarn.lock ./yarn.lock
    #docker cp vw_dev-update_npm-1:/frontend/package.json ./frontend/package.json
    #docker cp vw_dev-update_npm-1:/frontend/yarn.lock ./frontend/yarn.lock

#commands part 3, at your individual containers' .dockerfile:
    #RUN npm install --verbose
#==================================================================================


#why yarn:
    #better algorithm, better error messages

#commands explanation:
    #download package checker --> perform check with ncu --> pass -u to update package.json --> run actual install at your containers
    #if you have issues at "yarn install --dry-run --check-files", try running it again

#potential errors:
    #warning " > vue-loader@17.4.2" has unmet peer dependency "webpack@^4.1.0 || ^5.0.0-0".
        #fix:
            #just copy the whole "package info" thing, then run: yarn add
            #use -D if it's for dev packages
            #e.g.:
                #yarn add -D "webpack@^4.1.0 || ^5.0.0-0" "vite@^5.0.0 || ^6.0.0 || ^7.0.0" "vue-eslint-parser@^10.0.0"