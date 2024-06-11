FROM node:current

EXPOSE 8080

WORKDIR /frontend

#build context is at root
COPY ./frontend/package*.json ./
COPY ./frontend .

RUN npm install --verbose
RUN npm install -g vite --verbose

# CMD ["npm", "run", "dev"]

CMD ["sleep", "3600"]