<script setup>
import FriendList from '../components/contacts/FriendList.vue'
import TeamList from '../components/contacts/TeamList.vue'
</script>

<template>
  <div class="contacts-page">
    <div class="header-section">
      <h1>联系人与组队</h1>
    </div>

    <!-- Upper Section: Teams -->
    <section class="section-container team-container">
      <TeamList />
    </section>

    <!-- Lower Section: Friends -->
    <section class="section-container friend-container">
      <FriendList />
    </section>
  </div>
</template>

<style scoped>
.contacts-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px 16px;
  min-height: 100vh;
}

.header-section {
  text-align: center;
  margin-bottom: 24px;
}

.header-section h1 {
  font-size: 24px;
  color: #1e293b;
  font-weight: 700;
}

.section-container {
  margin-bottom: 32px;
}

/* Optional: Add a subtle divider or spacing */
.team-container {
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 32px;
}

@media (max-width: 640px) {
  .contacts-page {
    padding: 16px;
  }
}
</style>