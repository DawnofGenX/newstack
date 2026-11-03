<script setup lang="ts">
import { ref } from 'vue'

const count = ref(0)

function increment() {
  count.value += 1
}
</script>

<template>
  <div class="counter">
    <button type="button" @click="increment">count is {{! count }}</button>
    <p class="hint">Edit <code>src/components/Counter.vue</code> and save to test HMR.</p>
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

.hint {
  font-size: 0.85rem;
  opacity: 0.75;
}
</style>
