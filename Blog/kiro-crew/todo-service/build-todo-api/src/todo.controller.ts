import type { Request, Response } from 'express';
import { prisma } from './prisma-client';
import {
  CreateTodoSchema,
  UpdateTodoSchema,
  TodoIdParamSchema,
} from './todo.schema';
import { z } from 'zod';

// Translate a ZodError into a 400 response body.
function sendValidationError(res: Response, error: z.ZodError): Response {
  return res.status(400).json({
    error: 'ValidationError',
    details: error.issues.map((issue) => ({
      path: issue.path.join('.'),
      message: issue.message,
    })),
  });
}

// GET /todos
export async function listTodos(_req: Request, res: Response): Promise<Response> {
  const todos = await prisma.todo.findMany({ orderBy: { createdAt: 'desc' } });
  return res.status(200).json(todos);
}

// POST /todos
export async function createTodo(req: Request, res: Response): Promise<Response> {
  const parsed = CreateTodoSchema.safeParse(req.body);
  if (!parsed.success) {
    return sendValidationError(res, parsed.error);
  }

  const todo = await prisma.todo.create({ data: parsed.data });
  return res.status(201).json(todo);
}

// PUT /todos/:id
export async function updateTodo(req: Request, res: Response): Promise<Response> {
  const params = TodoIdParamSchema.safeParse(req.params);
  if (!params.success) {
    return sendValidationError(res, params.error);
  }

  const body = UpdateTodoSchema.safeParse(req.body);
  if (!body.success) {
    return sendValidationError(res, body.error);
  }

  const existing = await prisma.todo.findUnique({ where: { id: params.data.id } });
  if (!existing) {
    return res.status(404).json({ error: 'NotFound', message: 'Todo not found' });
  }

  const todo = await prisma.todo.update({
    where: { id: params.data.id },
    data: body.data,
  });
  return res.status(200).json(todo);
}

// DELETE /todos/:id
export async function deleteTodo(req: Request, res: Response): Promise<Response> {
  const params = TodoIdParamSchema.safeParse(req.params);
  if (!params.success) {
    return sendValidationError(res, params.error);
  }

  const existing = await prisma.todo.findUnique({ where: { id: params.data.id } });
  if (!existing) {
    return res.status(404).json({ error: 'NotFound', message: 'Todo not found' });
  }

  await prisma.todo.delete({ where: { id: params.data.id } });
  return res.status(204).send();
}
