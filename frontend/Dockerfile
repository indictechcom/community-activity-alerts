FROM node:lts-alpine
WORKDIR /src
COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173


ENV VITE_BACKEND_URL=http://localhost:5000

CMD ["npm", "run", "dev", "--", "--host"]