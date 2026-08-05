import { describe, it, expect } from 'vitest';
import {
  CreateTodoSchema,
  UpdateTodoSchema,
  TodoIdParamSchema,
} from './todo.schema';

describe('CreateTodoSchema', () => {
  it('accepts a valid payload', () => {
    const result = CreateTodoSchema.safeParse({
      title: 'Buy milk',
      description: 'From the store',
      completed: false,
    });
    expect(result.success).toBe(true);
  });

  it('accepts a payload with only a title', () => {
    const result = CreateTodoSchema.safeParse({ title: 'Just a title' });
    expect(result.success).toBe(true);
  });

  it('rejects a missing title', () => {
    const result = CreateTodoSchema.safeParse({ description: 'no title' });
    expect(result.success).toBe(false);
  });

  it('rejects an empty title', () => {
    const result = CreateTodoSchema.safeParse({ title: '   ' });
    expect(result.success).toBe(false);
  });
});

describe('UpdateTodoSchema', () => {
  it('accepts a partial update', () => {
    const result = UpdateTodoSchema.safeParse({ completed: true });
    expect(result.success).toBe(true);
  });

  it('rejects an empty object', () => {
    const result = UpdateTodoSchema.safeParse({});
    expect(result.success).toBe(false);
  });

  it('allows description to be null', () => {
    const result = UpdateTodoSchema.safeParse({ description: null });
    expect(result.success).toBe(true);
  });
});

describe('TodoIdParamSchema', () => {
  it('accepts a valid uuid', () => {
    const result = TodoIdParamSchema.safeParse({
      id: '3f3f0e2e-8a2a-4c3d-9b1e-2c9d4e5f6a7b',
    });
    expect(result.success).toBe(true);
  });

  it('rejects a non-uuid id', () => {
    const result = TodoIdParamSchema.safeParse({ id: 'not-a-uuid' });
    expect(result.success).toBe(false);
  });
});
