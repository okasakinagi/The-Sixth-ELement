# 用户信息提取模块

## 模块简介

用户信息提取模块（User Profile Extractor）是一个用于提取和拼接用户个人信息的服务，旨在为推荐系统提供结构化的用户画像数据。该模块从多个维度分析用户行为和特征，生成易于理解和使用的个人信息摘要。

## 核心功能

1. **用户兴趣分析**：提取用户的兴趣标签
2. **行为特征分析**：分析用户填写的问卷类型及数量
3. **活跃度分析**：评估用户的平台活跃度
4. **信用评分分析**：评估用户的信用等级
5. **最近活动分析**：分析用户最近的活跃情况
6. **积分获取渠道分析**：分析用户积分的主要来源
7. **注册时长分析**：计算用户的注册时长

## API 端点

### 获取用户个人信息摘要

- **端点**：`GET /api/v1/profile/summary`
- **认证**：需要 Bearer Token 认证
- **请求参数**：无
- **响应格式**：

```json
{
  "profile_summary": "用户兴趣：科技, 音乐, 旅行\n用户标签：北京大学\n已填问卷类型：市场调研(3), 用户体验(5), 学术研究(2)\n问卷填写总量：15，完成率：95%\n最近活跃：7天内\n用户活跃度：高（890/1000）\n信用评分：优秀（95/100）\n注册时长：6个月\n积分获取渠道：问卷填写(80%), 其他活动(20%)",
  "user": {
    "id": 1,
    "nickname": "张三",
    "email": "zhangsan@example.com"
  }
}
```

## 信息格式说明

生成的个人信息摘要包含以下字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| 用户兴趣 | 用户的兴趣标签 | 科技, 音乐, 旅行 |
| 用户标签 | 用户的其他标签（如学校、专业等） | 北京大学, 计算机科学 |
| 已填问卷类型 | 用户填写过的问卷类型及数量 | 市场调研(3), 用户体验(5) |
| 问卷填写总量 | 用户填写的问卷总数 | 15 |
| 完成率 | 用户问卷的完成率 | 95% |
| 最近活跃 | 用户最近的活跃情况 | 7天内 |
| 用户活跃度 | 用户的活跃度等级和分数 | 高（890/1000） |
| 信用评分 | 用户的信用等级和分数 | 优秀（95/100） |
| 注册时长 | 用户的注册时长 | 6个月 |
| 积分获取渠道 | 用户积分的主要来源及占比 | 问卷填写(80%), 其他活动(20%) |

## 技术实现

### 模块结构

```
user_profile_extractor/
├── __init__.py
├── controller/
│   ├── __init__.py
│   └── profile_extractor_controller.py  # API 控制器
├── service/
│   ├── __init__.py
│   └── profile_extractor_service.py     # 核心业务逻辑
├── mapper/
│   └── __init__.py
└── README.md
```

### 核心类和方法

#### ProfileExtractorService

- **extract_user_profile(user_id)**：提取用户个人信息并拼接成字符串
- **_analyze_survey_types(surveys)**：分析用户填写的问卷类型及数量
- **_calculate_completion_rate(all_responses, completed_responses)**：计算问卷完成率
- **_analyze_last_activity(user, completed_responses)**：分析用户最近活动
- **_analyze_points_channels(user)**：分析用户积分获取渠道
- **_calculate_registration_duration(user)**：计算用户注册时长
- **_build_profile_string(...)**：构建个人信息字符串

#### profile_extractor_controller.py

- **get_user_profile_summary(request)**：处理获取用户个人信息摘要的 HTTP 请求

## 推荐系统集成

该模块生成的个人信息摘要可直接用于推荐系统：

1. **作为大模型输入**：将摘要字符串作为提示词的一部分，让大模型分析用户特征
2. **结构化推荐**：基于摘要中的用户兴趣、问卷类型偏好等信息进行推荐
3. **个性化排序**：根据用户活跃度、信用评分等因素调整推荐顺序

## 使用示例

### 后端调用

```python
from user_profile_extractor.service.profile_extractor_service import ProfileExtractorService

# 创建服务实例
service = ProfileExtractorService()

# 提取用户个人信息
user_id = 1
profile_summary = service.extract_user_profile(user_id)

print(profile_summary)
```

### 前端调用

```javascript
// 使用 fetch API 调用
async function getUserProfileSummary() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    throw new Error('未登录');
  }

  const response = await fetch('/api/v1/profile/summary', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  if (!response.ok) {
    throw new Error('获取个人信息失败');
  }

  return await response.json();
}

// 使用示例
try {
  const result = await getUserProfileSummary();
  console.log('个人信息摘要:', result.profile_summary);
} catch (error) {
  console.error('错误:', error);
}
```

## 依赖关系

- **Django**：Web 框架
- **Django ORM**：数据库操作
- **core 模块**：用户模型、认证功能

## 扩展建议

1. **添加更多用户特征**：如用户的设备信息、地域信息等
2. **增强分析能力**：添加更复杂的用户行为分析算法
3. **支持导出格式**：支持 JSON、CSV 等多种格式的导出
4. **添加缓存机制**：减少重复计算，提高性能

## 注意事项

1. 该模块需要用户已登录才能使用
2. 首次调用可能会较慢，因为需要分析大量历史数据
3. 建议定期更新用户信息摘要，以反映用户的最新状态
