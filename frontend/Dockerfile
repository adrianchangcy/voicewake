FROM node:current

#Vite default port
EXPOSE ${VITE_PORT}

WORKDIR .

# #build context is at root
COPY ./frontend ./
COPY ./voicewake ./

WORKDIR /frontend

#attempt to fix "ERR_SSL_CIPHER_OPERATION_FAILED"
#used to work, but now have to on/off airplane mode to reset WiFi and ensure it works
RUN npm cache clear --force

#attempt to fix "ERR_SSL_CIPHER_OPERATION_FAILED"
#has worked once so far
RUN npm cache verify

RUN npm install --verbose
RUN npm install -g vite


# #file change at host is detected by Vite in container, so no further flags needed
#must use "sh" "-c", otherwise, if not sh, $var is interpreted as literal string instead of environment variable
CMD ["sh", "-c", "npm run dev -- --host 0.0.0.0 --port $VITE_PORT"]

#yarn, problem #1:
    #commands:
        # RUN yarn cache clean --all
        # RUN yarn install --verbose
        # RUN yarn global add vite
    #problem:
        #cipher operation failed
            #for npm, can fix with turning airplane mode on/off
    #solution:
        #delete yarn.lock
        #revert to npm, do npm install in update container, copy out package-lock.json