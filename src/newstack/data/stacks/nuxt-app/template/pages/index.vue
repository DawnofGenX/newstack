<script setup lang="ts">
import { computed, ref } from "vue";
import { stats } from "../lib/counts";

const text = ref("a b\n");
const counts = computed(() => stats(text.value));
</script>

<template>
  <main data-app="stats">
    <h1>{{ npm_name }}</h1>
    <p>Server-rendered on every request: the counters are computed twice.</p>
    <textarea v-model="text" rows="4" cols="48" aria-label="text" />
    <dl>
      <dt>lines</dt>
      <dd data-testid="lines" v-text="counts.lines" />
      <dt>words</dt>
      <dd data-testid="words" v-text="counts.words" />
      <dt>bytes</dt>
      <dd data-testid="bytes" v-text="counts.bytes" />
    </dl>
  </main>
</template>
