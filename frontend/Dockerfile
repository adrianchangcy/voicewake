FROM node:current-alpine

EXPOSE 8080

WORKDIR /frontend

COPY ./package*.json .

RUN npm install
RUN npm install -g @vue/cli

COPY . .