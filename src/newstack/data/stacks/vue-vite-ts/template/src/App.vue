<script setup lang="ts">
import Counter from './components/Counter.vue'

const title = '{{ title }}'
const description = '{{ description }}'
</script>

<template>
  <main>
    <h1>{{ title }}</h1>
    <p class="description">{{ description }}</p>
    <Counter />
  </main>
</template>

<style scoped>
main {
  max-width: 42rem;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

h1 {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.description {
  color: var(--color-text);
  margin-bottom: 2rem;
}
</style>
