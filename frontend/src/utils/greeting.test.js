import test from 'node:test';
import assert from 'node:assert/strict';
import { getGreetingText, getGreetingMeta } from './greeting.js';

test('uses morning greeting in Kolkata before noon', () => {
  const now = new Date('2026-09-20T08:30:00+05:30');
  const greeting = getGreetingText('Sarbajit Jana', now);
  assert.equal(greeting, 'Good morning, Sarbajit Jana. How can I help you?');
  assert.equal(getGreetingMeta(now).label, 'morning');
});

test('uses evening greeting at noon and in the afternoon', () => {
  const now = new Date('2026-09-20T12:00:00+05:30');
  const greeting = getGreetingText('Rahul Das', now);
  assert.equal(greeting, 'Good evening, Rahul Das. How can I help you?');
  assert.equal(getGreetingMeta(now).label, 'evening');
});

test('uses night greeting after 9pm', () => {
  const now = new Date('2026-09-20T21:30:00+05:30');
  const greeting = getGreetingText('Priya', now);
  assert.equal(greeting, 'Good night, Priya. How can I help you?');
  assert.equal(getGreetingMeta(now).label, 'night');
});
