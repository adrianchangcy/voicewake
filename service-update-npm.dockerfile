FROM node:current-alpine

#tailwind

WORKDIR .

COPY ./package.json ./
# COPY ./yarn.lock ./

#frontend

WORKDIR ./frontend

COPY ./frontend/package.json ./

COPY ./frontend/package-lock.json ./
# COPY ./frontend/yarn.lock ./

WORKDIR ../

#keep container alive
CMD ["sh", "-c", "echo 'Container is running...'; sleep infinity"]


#==================================================================================
#commands part 1, in container:
    #use better package manager
        #npm install -g yarn
    #install you packages
        #yarn install your-package
        #yarn install your-package-used-only-in-dev --save-dev
    #install update checker
        #yarn install -g npm-check-updates
    #perform checks, dry-run install, test install
        #ncu
        #ncu -u
        #yarn install --dry-run --check-files
        #npm install
        #cd frontend
        #ncu
        #ncu -u
        #yarn install --dry-run --check-files
        #npm install

#commands part 2, at host machine project root, cmd:
    #docker cp vw_dev-update_npm-1:/package.json ./package.json
    #docker cp vw_dev-update_npm-1:/package-lock.json ./package-lock.json
    #docker cp vw_dev-update_npm-1:/frontend/package.json ./frontend/package.json
    #docker cp vw_dev-update_npm-1:/frontend/package-lock.json ./frontend/package-lock.json

#commands part 3, at your individual containers' .dockerfile:
    #RUN npm install --verbose
#==================================================================================


#why yarn:
    #better algorithm, better error messages, much easier to fix peer dependency errors

#commands explanation:
    #download package checker --> perform check with ncu --> pass -u to update package.json --> run actual install at your containers
    #if you have issues at "yarn install --dry-run --check-files", try running it again
    #for dev-only packages like tailwind, add --save-dev flag when you install the specific package
    #we use npm install instead of yarn install
        #yarn's "cipher failed" error cannot be fixed, while npm can via airplane mode on+off
        #we use npm install here to get package-lock.json, and we don't want yarn.lock

#potential errors:
    #warning " > vue-loader@17.4.2" has unmet peer dependency "webpack@^4.1.0 || ^5.0.0-0".
        #fix:
            #just copy the whole "package info" thing, then run: yarn add
            #use -D if it's for dev packages
            #e.g.:
                #yarn add -D "webpack@^4.1.0 || ^5.0.0-0" "vite@^5.0.0 || ^6.0.0 || ^7.0.0" "vue-eslint-parser@^10.0.0"