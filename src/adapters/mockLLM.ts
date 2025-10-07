import { IAction } from '../types';

export async function mockGenerateAction(npc: any): Promise<IAction> {
  return { type: 'noop', description: 'no-op decision for test', changes: {} };
}
