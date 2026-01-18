<template>
  <div class="about">
    <h1>This is an about page</h1>
  </div>
</template>

<style scoped>
.about {
  min-height: 100vh;
  padding: 48px;
  display: flex;
  align-items: center;
}

@media (max-width: 768px) {
  .about {
    padding: 24px;
    align-items: flex-start;
  }
}
</style>
