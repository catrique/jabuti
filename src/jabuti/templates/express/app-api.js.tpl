import express from 'express';

export function createApp() {
  const app = express();

  app.use(allowFrontendOrigins(readFrontendOrigins()));
  app.use(express.json());

  app.get('/health', (_request, response) => {
    response.json({ status: 'ok' });
  });

  return app;
}

// Browser origins allowed to call the API, comma-separated. Set
// FRONTEND_ORIGINS in each environment; the default only covers local work.
function readFrontendOrigins() {
  return (process.env.FRONTEND_ORIGINS ?? '%%FRONTEND_ORIGINS%%')
    .split(',')
    .map((origin) => origin.trim())
    .filter(Boolean);
}

function allowFrontendOrigins(origins) {
  return (request, response, next) => {
    const origin = request.get('Origin');
    if (origin && origins.includes(origin)) {
      response.set({
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
        Vary: 'Origin',
      });
    }
    if (request.method === 'OPTIONS') {
      response.sendStatus(204);
      return;
    }
    next();
  };
}
