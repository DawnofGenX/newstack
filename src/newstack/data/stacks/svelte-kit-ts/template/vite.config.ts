import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig(({ mode }) => ({
	plugins: [
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},
			// Static site generation: every page is prerendered into build/.
			adapter: adapter()
		})
	],
	// Vitest runs with mode === 'test'. Resolve browser entry points there so `mount`
	// works against jsdom instead of Node/SSR. Reading `process.env` here would need
	// Node's types in a file that is type-checked by svelte-check, which is not guaranteed.
	resolve: mode === 'test' ? { conditions: ['browser'] } : undefined,
	test: {
		environment: 'jsdom',
		include: ['src/**/*.test.ts'],
		setupFiles: ['src/vitest-setup.ts']
	}
}));
