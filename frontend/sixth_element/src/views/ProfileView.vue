<template>
  <div class="profile">
    <header>
      <RouterLink class="back" to="/surveys">返回问卷管理</RouterLink>
      <h1>个人信息</h1>
      <p>示例页面：用于承载头像跳转入口。</p>
    </header>
    <section class="card">
      <div>
        <p class="label">昵称</p>
        <p class="value">PL</p>
      </div>
      <div>
        <p class="label">账号类型</p>
        <p class="value">企业管理员</p>
      </div>
      <div>
        <p class="label">积分余额</p>
        <p class="value">1,240</p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.profile {
  min-height: 100vh;
  padding: 48px;
  background: radial-gradient(circle at top, #f0f5ff 0%, #ffffff 55%);
}

header {
  display: grid;
  gap: 8px;
  margin-bottom: 24px;
}

h1 {
  font-family: 'Newsreader', serif;
  font-size: 32px;
}

.back {
  color: #1e4fb4;
  font-weight: 600;
}

.card {
  background: #ffffff;
  padding: 24px;
  border-radius: 18px;
  box-shadow: 0 16px 30px rgba(16, 35, 63, 0.1);
  display: grid;
  gap: 16px;
  max-width: 420px;
}

.label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: #6a7d95;
}

.value {
  font-weight: 600;
  font-size: 18px;
}
</style>
