# Use Node.js image for building
FROM node:14 as build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install frontend dependencies
RUN npm install

# Copy frontend source files
COPY . .

# Build frontend
RUN npm run build

# Use NGINX to serve the built frontend
FROM nginx:alpine

# Copy built frontend files
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
