<script lang="ts">
	let { step = 1 }: { step?: number } = $props();

	let count = $state(0);
</script>

<p class="count" role="status" aria-live="polite">Count: {count}</p>
<button type="button" onclick={() => (count += step)}>Increment</button>

<style>
  button {
    font: inherit;
    padding: 0.5rem 1.25rem;
    border-radius: 0.5rem;
    border: 1px solid currentColor;
    background: transparent;
    cursor: pointer;
  }

  button:hover {
    opacity: 0.85;
  }

  button:focus-visible {
    outline: 2px solid currentColor;
    outline-offset: 2px;
  }
</style>
