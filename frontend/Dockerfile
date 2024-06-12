FROM node:current

#Vite default port
EXPOSE 5173

WORKDIR /frontend

#build context is at root
COPY ./frontend/package*.json ./
COPY ./frontend .

RUN npm install --verbose
RUN npm install -g vite --verbose

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]