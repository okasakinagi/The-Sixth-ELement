<template>
  <div class="hall">
    <header class="hall-header">
      <div>
        <p class="kicker">Task Hub</p>
        <h1>任务大厅</h1>
        <p class="subtitle">集中查看任务、问卷和数据流转。</p>
      </div>
      <RouterLink class="cta" to="/surveys">进入问卷管理</RouterLink>
    </header>

    <section class="hall-grid">
      <article class="hall-card">
        <h2>问卷管理</h2>
        <p>管理问卷的全生命周期，从创建到分析。</p>
        <RouterLink class="link" to="/surveys">打开问卷管理</RouterLink>
      </article>
      <article class="hall-card muted">
        <h2>任务市场</h2>
        <p>查看推荐任务、积分兑换与投放情况。</p>
        <span class="link muted">即将上线</span>
      </article>
      <article class="hall-card muted">
        <h2>个人中心</h2>
        <p>账号信息、积分流水、系统设置。</p>
        <RouterLink class="link" to="/profile">前往个人信息</RouterLink>
      </article>
    </section>
  </div>
</template>

<style scoped>
.hall {
  min-height: 100vh;
  padding: 48px;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
}

.hall-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  margin-bottom: 36px;
}

.kicker {
  text-transform: uppercase;
  letter-spacing: 0.3em;
  font-size: 11px;
  color: #5b6d86;
}

h1 {
  font-family: 'Newsreader', serif;
  font-size: 34px;
  margin: 6px 0;
}

.subtitle {
  color: #637089;
}

.cta {
  background: linear-gradient(135deg, #2665d4, #4f80f1);
  color: #ffffff;
  padding: 12px 22px;
  border-radius: 999px;
  font-weight: 600;
}

.hall-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.hall-card {
  background: #ffffff;
  padding: 24px;
  border-radius: 20px;
  box-shadow: 0 14px 30px rgba(16, 35, 63, 0.12);
  display: grid;
  gap: 12px;
}

.hall-card h2 {
  font-size: 20px;
}

.hall-card p {
  color: #66788f;
}

.link {
  color: #1e4fb4;
  font-weight: 600;
}

.muted {
  opacity: 0.7;
}

@media (max-width: 720px) {
  .hall {
    padding: 28px;
  }

  .hall-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
