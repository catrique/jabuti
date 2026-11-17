import { existsSync } from 'node:fs';

import { createApp } from './app.js';

if (existsSync('.env')) {
  process.loadEnvFile();
}

const port = Number(process.env.PORT ?? 3000);

createApp().listen(port, () => {
  console.log(`Servidor ouvindo na porta ${port}`);
});
