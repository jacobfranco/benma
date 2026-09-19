import React from 'react';
import { act, create } from 'react-test-renderer';
import { router } from 'expo-router';

import HomeScreen from '@/app/index';
jest.mock('expo-router', () => ({ router: { push: jest.fn() } }));
jest.mock('@/auth/AuthProvider', () => ({ useAuth: () => ({ state: { phase: 'signed_in' }, signOut: jest.fn() }) }));

it('presents Conversation and Practice as the only primary speech modes', async () => {
  let renderer!: ReturnType<typeof create>;
  await act(async () => { renderer = create(React.createElement(HomeScreen)); });
  const labels = renderer.root.findAll((node) => Boolean(node.props.accessibilityLabel))
    .map((node) => node.props.accessibilityLabel);
  expect(labels).toContain('Open Conversation');
  expect(labels).toContain('Open Practice');
  expect(labels).not.toContain('Open perception');
  expect(labels).not.toContain('Open pronunciation');
  expect(labels).not.toContain('Open Free Talk');
  renderer.root.findByProps({ accessibilityLabel: 'Open Conversation' }).props.onPress();
  expect(router.push).toHaveBeenCalledWith('/conversation');
  renderer.root.findByProps({ accessibilityLabel: 'Open Practice' }).props.onPress();
  expect(router.push).toHaveBeenCalledWith('/practice');
  await act(async () => renderer.unmount());
});
