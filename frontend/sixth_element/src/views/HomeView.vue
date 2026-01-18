<script setup>
import TheWelcome from '../components/TheWelcome.vue'
</script>

<template>
  <main class="home">
    <TheWelcome />
  </main>
</template>

<style scoped>
.home {
  min-height: 100vh;
  padding: 48px;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
}
</style>
