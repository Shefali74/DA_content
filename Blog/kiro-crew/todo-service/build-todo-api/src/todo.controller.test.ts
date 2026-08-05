import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { Request, Response } from 'express';

// Mock the Prisma client module before importing the controller.
vi.mock('./prisma-client', () => {
  return {
    prisma: {
      todo: {
        findMany: vi.fn(),
        findUnique: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
        delete: vi.fn(),
      },
    },
  };
});

import { prisma } from './prisma-client';
import {
  listTodos,
  createTodo,
  updateTodo,
  deleteTodo,
} from './todo.controller';

// Minimal Response test double capturing status/json/send calls.
function mockResponse(): Response {
  const res = {} as Response;
  res.status = vi.fn().mockReturnValue(res);
  res.json = vi.fn().mockReturnValue(res);
  res.send = vi.fn().mockReturnValue(res);
  return res;
}

const VALID_ID = '3f3f0e2e-8a2a-4c3d-9b1e-2c9d4e5f6a7b';

const sampleTodo = {
  id: VALID_ID,
  title: 'Buy milk',
  description: null,
  completed: false,
  createdAt: new Date('2026-01-01T00:00:00.000Z'),
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe('listTodos', () => {
  it('returns 200 with all todos', async () => {
    (prisma.todo.findMany as ReturnType<typeof vi.fn>).mockResolvedValue([
      sampleTodo,
    ]);
    const req = {} as Request;
    const res = mockResponse();

    await listTodos(req, res);

    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith([sampleTodo]);
  });
});

describe('createTodo', () => {
  it('creates and returns 201 for a valid body', async () => {
    (prisma.todo.create as ReturnType<typeof vi.fn>).mockResolvedValue(
      sampleTodo,
    );
    const req = { body: { title: 'Buy milk' } } as Request;
    const res = mockResponse();

    await createTodo(req, res);

    expect(prisma.todo.create).toHaveBeenCalledWith({
      data: { title: 'Buy milk' },
    });
    expect(res.status).toHaveBeenCalledWith(201);
    expect(res.json).toHaveBeenCalledWith(sampleTodo);
  });

  it('returns 400 for an invalid body', async () => {
    const req = { body: {} } as Request;
    const res = mockResponse();

    await createTodo(req, res);

    expect(res.status).toHaveBeenCalledWith(400);
    expect(prisma.todo.create).not.toHaveBeenCalled();
  });
});

describe('updateTodo', () => {
  it('updates an existing todo and returns 200', async () => {
    (prisma.todo.findUnique as ReturnType<typeof vi.fn>).mockResolvedValue(
      sampleTodo,
    );
    (prisma.todo.update as ReturnType<typeof vi.fn>).mockResolvedValue({
      ...sampleTodo,
      completed: true,
    });
    const req = {
      params: { id: VALID_ID },
      body: { completed: true },
    } as unknown as Request;
    const res = mockResponse();

    await updateTodo(req, res);

    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith({ ...sampleTodo, completed: true });
  });

  it('returns 404 when the todo does not exist', async () => {
    (prisma.todo.findUnique as ReturnType<typeof vi.fn>).mockResolvedValue(null);
    const req = {
      params: { id: VALID_ID },
      body: { completed: true },
    } as unknown as Request;
    const res = mockResponse();

    await updateTodo(req, res);

    expect(res.status).toHaveBeenCalledWith(404);
    expect(prisma.todo.update).not.toHaveBeenCalled();
  });

  it('returns 400 for an invalid id', async () => {
    const req = {
      params: { id: 'nope' },
      body: { completed: true },
    } as unknown as Request;
    const res = mockResponse();

    await updateTodo(req, res);

    expect(res.status).toHaveBeenCalledWith(400);
  });
});

describe('deleteTodo', () => {
  it('deletes an existing todo and returns 204', async () => {
    (prisma.todo.findUnique as ReturnType<typeof vi.fn>).mockResolvedValue(
      sampleTodo,
    );
    (prisma.todo.delete as ReturnType<typeof vi.fn>).mockResolvedValue(
      sampleTodo,
    );
    const req = { params: { id: VALID_ID } } as unknown as Request;
    const res = mockResponse();

    await deleteTodo(req, res);

    expect(prisma.todo.delete).toHaveBeenCalledWith({ where: { id: VALID_ID } });
    expect(res.status).toHaveBeenCalledWith(204);
  });

  it('returns 404 when the todo does not exist', async () => {
    (prisma.todo.findUnique as ReturnType<typeof vi.fn>).mockResolvedValue(null);
    const req = { params: { id: VALID_ID } } as unknown as Request;
    const res = mockResponse();

    await deleteTodo(req, res);

    expect(res.status).toHaveBeenCalledWith(404);
    expect(prisma.todo.delete).not.toHaveBeenCalled();
  });
});
