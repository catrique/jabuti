import path from 'node:path';

import express from 'express';

const projectRoot = path.join(import.meta.dirname, '..');

export function createApp() {
  const app = express();

  app.set('view engine', 'ejs');
  app.set('views', path.join(projectRoot, 'views'));
  app.use(express.static(path.join(projectRoot, 'public')));

  app.get('/', (_request, response) => {
    response.render('index', { projectName: '%%PROJECT_NAME%%' });
  });

  app.get('/health', (_request, response) => {
    response.json({ status: 'ok' });
  });

  return app;
}
