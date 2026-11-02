<script lang="ts">
	let { step = 1 }: { step?: number } = $props();

	let count = $state(0);
</script>

<button onclick={() => (count += step)}>Count is {count}</button>
