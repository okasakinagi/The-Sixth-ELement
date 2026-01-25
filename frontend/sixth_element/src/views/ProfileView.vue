<template>
  <div class="profile">
    <div class="profile-shell">
      <header class="header">
        <div class="title-block">
          <p class="kicker">Profile</p>
          <h1>个人信息</h1>
        </div>
        <div class="actions">
          <RouterLink class="ghost" to="/surveys">返回问卷管理</RouterLink>
        </div>
      </header>
      <section class="profile-grid">
        <div class="profile-card">
          <p class="label">昵称</p>
          <p class="value">PL</p>
        </div>
        <div class="profile-card">
          <p class="label">账号类型</p>
          <p class="value">企业管理员</p>
        </div>
        <div class="profile-card">
          <p class="label">积分余额</p>
          <p class="value">1,240</p>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.profile {
  min-height: 100vh;
  padding: 12px 10px 20px;
  background: #f6f8fb;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.profile-shell {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.header {
  background: #ffffff;
  border: 1px solid #e3e9f5;
  border-radius: 14px;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  box-shadow: 0 6px 20px rgba(0, 82, 217, 0.05);
}

.title-block h1 {
  margin: 2px 0 0;
  font-size: 22px;
  color: #0b2b66;
  font-weight: 700;
}

.kicker {
  text-transform: uppercase;
  letter-spacing: 0.24em;
  font-size: 11px;
  color: #5c7599;
  margin: 0;
}

.actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ghost {
  border: 1px solid #0052d9;
  color: #0052d9;
  background: #ffffff;
  padding: 8px 14px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.ghost:hover {
  background: #0052d9;
  color: #ffffff;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: #5c7599;
  margin: 0 0 6px;
}

.value {
  font-weight: 600;
  font-size: 18px;
  color: #0b2b66;
  margin: 0;
}

.profile-card {
  background: #ffffff;
  border: 1px solid #e3e9f5;
  border-radius: 14px;
  padding: 16px;
  box-shadow: 0 8px 20px rgba(0, 82, 217, 0.05);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

@media (max-width: 640px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
