import { Router } from 'express';
import {
  listTodos,
  createTodo,
  updateTodo,
  deleteTodo,
} from './todo.controller';

export const todoRouter = Router();

todoRouter.get('/', listTodos);
todoRouter.post('/', createTodo);
todoRouter.put('/:id', updateTodo);
todoRouter.delete('/:id', deleteTodo);
