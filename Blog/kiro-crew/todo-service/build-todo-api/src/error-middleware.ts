import type { NextFunction, Request, Response } from 'express';

// 404 handler for unmatched routes. Registered after all routes so it only
// runs when nothing else matched.
export function notFoundHandler(_req: Request, res: Response): Response {
  return res.status(404).json({
    error: 'NotFound',
    message: 'Route not found',
  });
}

// Centralized error handler. Ensures the JSON API always responds with a JSON
// body (never an HTML stack trace) when a handler throws or a promise rejects
// — e.g. the database being unreachable. Must keep all four parameters so
// Express recognizes it as an error-handling middleware.
export function errorHandler(
  err: unknown,
  _req: Request,
  res: Response,
  _next: NextFunction,
): Response {
  // Avoid leaking internals to clients; log the real error server-side.
  console.error(err);
  return res.status(500).json({
    error: 'InternalServerError',
    message: 'An unexpected error occurred',
  });
}
