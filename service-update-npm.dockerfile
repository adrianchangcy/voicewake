FROM node:current-alpine

#tailwind

WORKDIR .

COPY ./package*.json ./

# RUN npm install --verbose

#frontend

WORKDIR ./frontend

COPY ./frontend/package*.json ./

WORKDIR ../

#install update checker
CMD ["sh", "-c", "npm install -g npm-check-updates"]


#keep container alive
CMD ["sh", "-c", "echo 'Container is running...'; sleep infinity"]
