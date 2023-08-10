const http = require('http');

const server = http.createServer((req, res) => {
  // Allow CORS by setting appropriate headers
 res.setHeader('Content-Type', 'application/json');
    res.setHeader('Access-Control-Allow-Origin', 'http://localhost:8080'); // Replace with your frontend's URL
    res.setHeader('Access-Control-Allow-Methods', 'GET');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.url === '/api/data' && req.method === 'GET') {

    res.end(JSON.stringify({ message: 'Hello from the server!' }));
  } else {
    res.statusCode = 404;
    res.end('Not Found');
  }
});

const PORT = 3002;
server.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
