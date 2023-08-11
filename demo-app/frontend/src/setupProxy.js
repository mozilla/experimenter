// src/setupProxy.js
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
      createProxyMiddleware({
      target: process.env.DEMO_APP_SERVER??'http://localhost:3002',
      changeOrigin: true,
    })
  );
};
