import { describe, it, expect, vi } from 'vitest';
import type { NextFunction, Request, Response } from 'express';
import { errorHandler, notFoundHandler } from './error-middleware';

function mockResponse(): Response {
  const res = {} as Response;
  res.status = vi.fn().mockReturnValue(res);
  res.json = vi.fn().mockReturnValue(res);
  return res;
}

describe('notFoundHandler', () => {
  it('responds 404 with a JSON body', () => {
    const res = mockResponse();

    notFoundHandler({} as Request, res);

    expect(res.status).toHaveBeenCalledWith(404);
    expect(res.json).toHaveBeenCalledWith({
      error: 'NotFound',
      message: 'Route not found',
    });
  });
});

describe('errorHandler', () => {
  it('responds 500 with a JSON body and does not leak internals', () => {
    const res = mockResponse();
    const spy = vi.spyOn(console, 'error').mockImplementation(() => undefined);

    errorHandler(
      new Error('DB unreachable: connect ECONNREFUSED 127.0.0.1:5432'),
      {} as Request,
      res,
      (() => undefined) as NextFunction,
    );

    expect(res.status).toHaveBeenCalledWith(500);
    expect(res.json).toHaveBeenCalledWith({
      error: 'InternalServerError',
      message: 'An unexpected error occurred',
    });
    spy.mockRestore();
  });
});
