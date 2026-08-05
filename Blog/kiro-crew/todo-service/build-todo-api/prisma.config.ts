import path from 'node:path';
import { defineConfig } from 'prisma/config';

// Keep the schema in prisma/ but store migrations in db/migrations/ per the
// project constraint that migrations must NOT live under scripts/.
export default defineConfig({
  schema: path.join('prisma', 'schema.prisma'),
  migrations: {
    path: path.join('db', 'migrations'),
  },
});
