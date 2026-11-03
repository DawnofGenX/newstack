<script setup lang="ts">
import { ref } from 'vue'

const count = ref(0)

function increment() {
  count.value += 1
}
</script>

<template>
  <div class="counter">
    <p class="count" role="status" aria-live="polite">Count: {{! count }}</p>
    <button type="button" @click="increment">Increment</button>
  </div>
</template>

<style scoped>
.counter {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

button {
  font-size: 1rem;
  padding: 0.5rem 1rem;
  border-radius: 0.4rem;
  border: 1px solid var(--color-border);
  background-color: var(--color-background-soft);
  color: var(--color-text);
  cursor: pointer;
}

button:hover {
  border-color: hsla(160, 100%, 37%, 1);
}

button:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}

.hint {
  font-size: 0.85rem;
}
</style>
