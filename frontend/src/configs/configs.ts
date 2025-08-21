import { createEnv } from '@t3-oss/env-core';
import { z } from 'zod';

export const configs = createEnv({
  // Add server variables here
  server: {},
  clientPrefix: 'NEXT_PUBLIC_',
  // Add client variables here (must be prefixed with NEXT_PUBLIC_)
  client: {
    NEXT_PUBLIC_BACKEND_URL: z.url(),
    NEXT_PUBLIC_ENVIRONMENT: z
      .enum(['development', 'production'])
      .default('development'),
    NEXT_PUBLIC_APP_DOMAIN: z.string().default('localhost'),
  },
  runtimeEnvStrict: {
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL,
    NEXT_PUBLIC_ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT,
    NEXT_PUBLIC_APP_DOMAIN: process.env.NEXT_PUBLIC_APP_DOMAIN,
  },
});
