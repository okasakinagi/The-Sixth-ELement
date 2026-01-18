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
      <article class="hall-card">
        <h2>积分记录</h2>
        <p>查看你的积分收支和荣誉勋章。</p>
        <RouterLink class="link" to="/points">查看积分详情</RouterLink>
      </article>
      <article class="hall-card">
        <h2>个人中心</h2>
        <p>账号信息、个人资料、系统设置。</p>
        <RouterLink class="link" to="/profile">前往个人信息</RouterLink>
      </article>
    </section>
  </div>
</template>

<script setup>
// 无需额外脚本
</script>

<style scoped>
.hall {
  min-height: 100vh;
  background: radial-gradient(circle at top left, #edf3ff 0%, #f7f9ff 45%, #ffffff 100%);
  padding: 48px;
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
  text-decoration: none;
  transition: all 0.3s ease;
}

.cta:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(30, 79, 180, 0.3);
}

.hall-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.hall-card {
  background: #ffffff;
  padding: 28px;
  border-radius: 16px;
  box-shadow: 0 2px 8px rgba(16, 35, 63, 0.08);
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.3s ease;
  border: 1px solid #e8eef5;
}

.hall-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(16, 35, 63, 0.12);
  border-color: #d0d8e0;
}

.hall-card h2 {
  font-size: 20px;
  color: #1a202c;
  margin: 0;
}

.hall-card p {
  color: #66788f;
  font-size: 14px;
  margin: 0;
}

.link {
  color: #1e4fb4;
  font-weight: 600;
  text-decoration: none;
  margin-top: 8px;
  display: inline-block;
  transition: all 0.2s ease;
}

.link:hover {
  color: #1a3f8a;
  text-decoration: underline;
}

@media (max-width: 768px) {
  .hall {
    padding: 32px 20px;
  }

  .hall-header {
    flex-direction: column;
    align-items: flex-start;
  }

  h1 {
    font-size: 28px;
  }

  .hall-grid {
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  }
}

@media (max-width: 480px) {
  .hall {
    padding: 24px 16px;
  }

  h1 {
    font-size: 24px;
  }

  .hall-grid {
    grid-template-columns: 1fr;
  }

  .hall-card {
    padding: 20px;
  }

  .cta {
    width: 100%;
    text-align: center;
  }
}
</style>
