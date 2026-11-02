<script lang="ts">
	import Counter from '#lib/Counter.svelte';
</script>

<svelte:head>
	<title>{{ title }}</title>
	<meta name="description" content="{{ description }}" />
</svelte:head>

<main>
	<h1>{{ title }}</h1>
	<p>{{ description }}</p>
	<Counter />
</main>

<style>
	main {
		max-width: 40rem;
		margin: 4rem auto;
		padding: 0 1rem;
		font-family:
			system-ui,
			-apple-system,
			sans-serif;
	}

	h1 {
		margin-bottom: 0.25rem;
	}

	p {
		margin-top: 0;
		color: #555;
	}
</style>
