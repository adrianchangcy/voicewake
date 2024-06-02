FROM node:current-alpine

EXPOSE 8080

WORKDIR /frontend

COPY ./frontend/package*.json ./

RUN npm install --verbose
RUN npm install -g @vue/cli --verbose

COPY . .