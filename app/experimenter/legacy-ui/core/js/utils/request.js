export async function request(url, options = {}, extraHeaders = {}) {
  let queryString = '';

  const headers = new Headers();
  headers.append('Accept', 'application/json');
  if (!(options.body && options.body instanceof FormData)) {
    headers.append('Content-Type', 'application/json');
  }

  for (let headerName in extraHeaders) {
    headers.append(headerName, extraHeaders[headerName]);
  }

  const settings = {
    headers,
    credentials: 'same-origin',
    method: 'GET',
    ...options,
  };

  // Convert `data` to `body` or querystring if necessary.
  if ('data' in settings) {
    if ('body' in settings) {
      throw new Error('Only pass one of `settings.data` and `settings.body`.');
    }

    if (['GET', 'HEAD'].includes(settings.method.toUpperCase())) {
      const queryStringData = Object.keys(settings.data).map(
        key => `${key}=${encodeURIComponent(settings.data[key])}`,
      );
      queryString = `?${queryStringData.join('&')}`;
    } else {
      settings.body = JSON.stringify(settings.data);
    }

    delete settings.data;
  }

  const response = await fetch(`${url}${queryString}`, settings);

  if (!response.ok) {
    let message;
    let data = {};
    let err;

    try {
      data = await response.json();
      message = data.detail || response.statusText;
    } catch (error) {
      message = `Invalid JSON in API Response: ${url}`;
      err = error;
    }

    data = { ...data, status: response.status };

    throw new RequestError(message, data, err);
  }

  if (response.status !== 204) {
    return response.json();
  }

  return null;
}

export function RequestError(message, data = {}) {
  this.data = data;
  this.message = message;
  this.stack = Error().stack;
}
RequestError.prototype = Object.create(Error.prototype);
RequestError.prototype.name = 'RequestError';
