# Personal Homepage Module - 个人主页模块

## 📋 概述

本模块实现了用户个人画像管理功能，采用**三层分层架构**（Controller-Service-Mapper），**基于Tag系统**提供用户画像的创建、查询、更新等功能。

> **设计理念：** 用户画像通过Tag标签系统实现，不使用独立的UserProfile表，而是复用core应用中的Tag/UserTag模型。这样既保持了数据一致性，又支持灵活的画像字段扩展。

## 🏗️ 架构设计

```
personal_homepage/
├── mapper/                # 数据访问层 (Mapper)
│   └── profile_mapper.py  - 封装Tag系统的数据操作
├── services/              # 业务逻辑层 (Service)
│   └── profile_service.py - 处理业务逻辑和数据验证
├── controllers/           # 控制器层 (Controller)
│   └── profile_controller.py - 处理HTTP请求/响应
├── urls.py               # 路由配置
├── apps.py               # Django应用配置
└── README.md             # 本文档
```

### 分层职责

#### 1. **数据模型** (core/models.py - 复用)
- **Tag模型** - 标签定义
  - `name`: 标签名称
  - `type`: 标签类型（gender/age/college/major/mbti/interest/skill等）
  - 支持的画像标签类型：
    - 单值：gender, age, grade, college, major, mbti, status
    - 多值：interest, organization, consumption, career, skill

- **UserTag模型** - 用户标签关联
  - `user`: 关联用户（FK → AppUser）
  - `tag`: 关联标签（FK → Tag）
  - 唯一约束：同一用户不能重复拥有同一标签

#### 2. **Mapper层** (mapper/profile_mapper.py)
- **UserProfileMapper类** - 数据访问映射器
#### 2. **Mapper层** (mapper/profile_mapper.py)
- **UserProfileMapper类** - 数据访问映射器
  - `get_user_tags(user, tag_type)` - 获取用户的标签
  - `get_user_profile_dict(user)` - 获取画像字典
  - `set_user_tag(user, tag_type, tag_name)` - 设置单个标签
  - `set_user_tags_multi(user, tag_type, tag_names)` - 设置多个标签
  - `update_user_profile(user, data)` - 更新画像
  - `delete_user_profile(user)` - 删除所有画像标签
  - `search_users_by_tags(criteria)` - 按标签搜索用户

#### 3. **Service层** (services/profile_service.py)
- **UserProfileService类** - 业务逻辑服务
  - `get_profile(user)` - 获取画像（含完成度计算）
  - `update_profile(user, data)` - 更新画像（含验证）
  - `replace_profile(user, data)` - 替换画像（含验证）
  - `_validate_profile_data(data, partial)` - 数据验证
  - `_calculate_completion(profile)` - 计算完成度
  - `search_matching_profiles(user, criteria)` - 匹配推荐

#### 4. **Controller层** (controllers/profile_controller.py)
- **API端点处理器**
  - `user_profile_handler` - 统一入口（根据HTTP方法路由）
  - `get_user_profile` - 处理GET请求
  - `update_user_profile` - 处理PATCH请求
  - `replace_user_profile` - 处理PUT请求
  - `search_matching_profiles` - 处理匹配搜索

---

## 🔌 API接口

### 1. 获取用户画像
```http
GET /api/v1/users/me/profile
Authorization: Bearer <token>
```

**响应示例：**
```json
{
  "user_id": 123,
  "gender": "female",
  "age": 20,
  "grade": "大二",
  "college": "计算机学院",
  "major": "计算机科学与技术",
  "mbti": "INTJ",
  "interests": "人工智能、德语",
  "organizations": "学生会、摄影社",
  "consumption_preferences": ["数码", "奶茶"],
  "career_intention": ["大厂"],
  "skills": ["Python", "视频剪辑"],
  "current_status": "备战期末",
  "profile_completion": 75,
  "updated_at": "2026-01-28T12:00:00Z"
}
```

### 2. 部分更新画像（PATCH）
```http
PATCH /api/v1/users/me/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "age": 21,
  "college": "物理学院",
  "skills": ["Python", "机器学习"]
}
```

**特点：**
- 只更新传入的字段
- 未传入的字段保持不变
- 自动重新计算完成度

### 3. 完整替换画像（PUT）
```http
PUT /api/v1/users/me/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "gender": "male",
  "age": 22,
  "grade": "大三",
  "college": "计算机学院",
  "major": "软件工程",
  "mbti": "ENTP",
  "interests": "开源、创业",
  "organizations": "技术社",
  "consumption_preferences": ["咖啡"],
  "career_intention": ["创业"],
  "skills": ["Java", "Go"],
  "current_status": "准备实习"
}
```

**特点：**
- 提交完整画像对象
- 未传入的字段会被置为NULL/默认值

### 4. 搜索匹配画像（推荐）
```http
GET /api/v1/users/me/profile/matches?college=计算机&min_completion=60
Authorization: Bearer <token>
```

**响应示例：**
```json
{
  "matches": [
    {
      "user_id": 456,
      "college": "计算机学院",
      "major": "人工智能",
      "mbti": "INTJ",
      "profile_completion": 80,
      ...
    }
  ]
}
```

---

## ✅ 数据验证规则

### 字段约束

| 字段 | 类型 | 长度限制 | 枚举值 |
|------|------|----------|--------|
| gender | string | - | male/female/other/secret |
| age | integer | 0-120 | - |
| grade | string | ≤10 | - |
| college | string | ≤50 | - |
| major | string | ≤50 | - |
| mbti | string | 4 | 16种MBTI类型 |
| interests | string | ≤200 | - |
| organizations | string | ≤200 | - |
| consumption_preferences | array | ≤20项 | 每项≤20字符 |
| career_intention | array | ≤20项 | 每项≤20字符 |
| skills | array | ≤20项 | 每项≤20字符 |
| current_status | string | ≤100 | - |

### 验证失败响应（422）

```json
{
  "error": {
    "code": "validation_error",
    "message": "参数校验失败",
    "details": {
      "age": ["Age must be between 0 and 120"],
      "major": ["Max length is 50"],
      "skills": ["Array length must be <= 20"]
    }
  }
}
```

---

## 🎯 核心特性

### 1. 基于Tag系统的灵活设计
- 画像字段以Tag类型区分（gender/age/college/major/mbti/interest等）
- 单值字段：每个类型只保留一个Tag（如gender, college）
- 多值字段：每个类型可有多个Tag（如interests, skills）
- 易于扩展：添加新画像字段只需定义新的Tag类型

### 2. 自动完成度计算
- Service层的`_calculate_completion()`方法计算完成度
- 完成度 = (已填写字段数 / 总字段数) × 100
- 数组字段为空时不计入已填写

### 3. 数据一致性保证
- 使用事务（`@transaction.atomic`）确保更新操作原子性
- 单值字段更新时自动删除旧值
- PUT操作先清空所有画像标签再设置新值

### 4. 标签复用与推荐
- Tag可被多个用户共享（如"计算机学院"标签）
- 支持按标签搜索用户（用于匹配推荐）
- 标签系统为任务大厅的推荐算法提供数据基础

---

## 🚀 部署步骤

### 1. 注册应用
已在 `module/survey_app/settings.py` 中添加：
```python
INSTALLED_APPS = [
    ...
    "personal_homepage",
]
```

### 2. 配置路由
已在 `module/survey_app/urls.py` 中添加：
```python
path("api/v1/", include("personal_homepage.urls")),
```

### 3. 无需数据库迁移
因为复用core应用的Tag/UserTag模型，无需为personal_homepage创建新的数据库表。

### 4. 测试API
```bash
# 启动服务器
python Main.py runserver

# 测试获取画像
curl -H "Authorization: Bearer <token>" \
  http://127.0.0.1:8000/api/v1/users/me/profile
```

---

## 🔧 扩展建议

### 1. 添加新的画像字段
```python
# 在mapper/profile_mapper.py中添加常量
TAG_TYPE_HOMETOWN = "hometown"

# 在get_user_profile_dict方法中添加字段映射
elif tag_type == UserProfileMapper.TAG_TYPE_HOMETOWN and not profile['hometown']:
    profile['hometown'] = tag_name
```

### 2. 增强匹配算法
- 基于MBTI相似度计算
- 基于兴趣标签交集（Tag.objects.filter(usertag__user=user1) & Tag.objects.filter(usertag__user=user2)）
- 引入协同过滤推荐

### 3. 标签热度统计
```python
# 统计最热门的标签
from django.db.models import Count
Tag.objects.annotate(user_count=Count('usertag')).order_by('-user_count')
```

---

## 📝 注意事项

1. **依赖core应用** - 必须确保core.Tag和core.UserTag模型已创建
2. **标签类型命名** - 新增标签类型时注意与Tag.TYPE_CHOICES保持一致
3. **数据迁移** - 若Tag.type字段的choices需要扩展，需在core/models.py中修改
4. **性能优化** - 高频查询建议为Tag.type和UserTag.user_id添加索引（已在core中实现）

---

## 🎨 设计亮点

✅ **复用Tag系统** - 避免数据冗余，画像与标签统一管理  
✅ **严格分层** - Mapper/Service/Controller职责清晰  
✅ **数据验证** - Service层统一验证，错误信息详细  
✅ **RESTful设计** - 语义清晰的HTTP方法（GET/PATCH/PUT）  
✅ **灵活扩展** - 添加新字段无需修改数据库结构  
✅ **事务安全** - 所有更新操作都有事务保护  

---

**实现完成时间：** 2026-01-28  
**遵循文档：** doc/api/API-个人界面.md + doc/ER文档.md（Tag系统设计）
