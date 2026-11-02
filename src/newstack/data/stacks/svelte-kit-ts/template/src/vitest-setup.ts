import { cleanup } from '@testing-library/svelte';
import { afterEach } from 'vitest';

// Unmount rendered components between tests so screen queries stay unambiguous.
afterEach(cleanup);
