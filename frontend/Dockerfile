FROM node:current

#Vite default port
EXPOSE ${VITE_PORT}

WORKDIR /frontend

# #build context is at root
COPY ./frontend/package*.json ./
COPY ./frontend .

#attempt to fix "ERR_SSL_CIPHER_OPERATION_FAILED"
#used to work, but now have to switch WiFi channels to ensure it works
RUN npm cache clear --force

#attempt to fix "ERR_SSL_CIPHER_OPERATION_FAILED"
#has worked once so far
RUN npm cache verify

RUN npm install --verbose
RUN npm install -g vite --verbose

# #file change at host is detected by Vite in container, so no further flags needed
#must use "sh" "-c", otherwise, if not sh, $var is interpreted as literal string instead of environment variable
CMD ["sh", "-c", "npm run dev -- --host 0.0.0.0 --port $VITE_PORT"]