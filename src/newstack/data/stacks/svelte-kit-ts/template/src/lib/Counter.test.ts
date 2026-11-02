import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import Counter from './Counter.svelte';

describe('Counter', () => {
	it('renders the initial count', () => {
		render(Counter);
		expect(screen.getByRole('button').textContent).toContain('Count is 0');
	});

	it('increments the count when clicked', async () => {
		render(Counter);
		const button = screen.getByRole('button');
		await fireEvent.click(button);
		expect(button.textContent).toContain('Count is 1');
	});
});
