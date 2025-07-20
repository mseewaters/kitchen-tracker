<template>
  <div class="home">
    <h1>Welcome to {{ projectName }}</h1>
    <p>Your serverless application is ready!</p>
  </div>
</template>

<script setup lang="ts">
const projectName = 'Your App'
</script>

<style scoped>
.home {
  padding: 2rem;
  text-align: center;
}
</style>