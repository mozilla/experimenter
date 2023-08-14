const http = require('http');

const server = http.createServer((req, res) => {


if (req.url === '/api/data' && req.method === 'GET') {
  res.setHeader('Content-Type', 'application/json');
  const jsonResponse = JSON.stringify({ message: 'Hello from the server!' });
  console.log('Server Response:', jsonResponse);
  res.end(jsonResponse);
} else {
  res.statusCode = 404;
  res.end('Not Found');
}
});

const PORT = 3002;
server.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
