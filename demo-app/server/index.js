const http = require('http');
const url = require('url');

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url, true);

  if (parsedUrl.pathname === '/api/data' && req.method === 'GET') {
    res.setHeader('Content-Type', 'application/json');

    const defaultApiInput = {
      client_id: '4a1d71ab-29a2-4c5f-9e1d-9d9df2e6e449',
      context: {
        key1: 'default-value1',
        key2: {
          'key2.1': 'default-value2',
          'key2.2': 'default-value3',
        },
      },
    };

    const clientID = req.headers['x-client-id'] || defaultApiInput.client_id;
    const contextJSON = req.headers['x-context'] || JSON.stringify(defaultApiInput.context);
    const context = JSON.parse(contextJSON);
    const nimbusPreview = parsedUrl.query.nimbus_preview === 'true';

    const apiInput = {
      client_id: clientID,
      context: context,
      nimbus_preview: nimbusPreview,
    };

    let pathName = '/v1/features/'
    if(nimbusPreview) {
      pathName= pathName+"?nimbus_preview=" + nimbusPreview;
    }
    const options = {
      hostname: 'cirrus',
      port: 8001,
      path: pathName,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const reqToOtherAPI = http.request(options, responseFromAPI => {
      let responseData = '';

      responseFromAPI.on('data', chunk => {
        responseData += chunk;
      });

      responseFromAPI.on('end', () => {
        res.end(responseData);
      });
    });

    reqToOtherAPI.on('error', error => {
      console.error('Error sending request to API:', error);
      res.statusCode = 500;
      res.end('Internal Server Error');
    });

    reqToOtherAPI.write(JSON.stringify(apiInput));
    reqToOtherAPI.end();
  } else {
    res.statusCode = 404;
    res.end('Not Found');
  }
});

const PORT = 3002;
server.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
