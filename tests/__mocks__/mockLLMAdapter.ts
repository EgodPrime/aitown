export function mockGenerateAction(npc: any) {
  // deterministic action for tests
  return Promise.resolve({
    type: 'noop',
    description: 'no-op decision for test',
    changes: {}
  });
}
