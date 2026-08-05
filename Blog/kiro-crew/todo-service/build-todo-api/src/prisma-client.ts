import { PrismaClient } from '@prisma/client';

// Reuse a single PrismaClient instance across the app. In development,
// store it on globalThis to avoid exhausting the connection pool when
// the module is re-evaluated (e.g. by tsx watch / HMR).
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ?? new PrismaClient();

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

export default prisma;
