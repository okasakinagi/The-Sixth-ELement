# 内部 API

本文档描述内部相似度和向量接口。它们主要供服务间调用，不建议直接暴露给普通前端。

## 约定

- Base URL：`/api/v1/internal`
- Content-Type：`application/json`
- 认证方式：Bearer Token

## 1. 相似度计算

### 计算用户与问卷相似度

`POST /similarity/compute`

请求体：

```json
{
  "user_id": "1",
  "survey_id": "34"
}
```

说明：

- 当前实现会重新计算，不按旧的缓存口径返回命中结果。
- 返回结果里的 `cached` 当前始终为 `false`。

## 2. 向量接口

### 生成向量文本

`POST /vector/generate-string`

说明：

- 这是占位接口。
- 当前实现返回的是简化文本，供后续向量化使用。

### 直接编码文本

`POST /vector/encode`

请求体：

```json
{
  "ref_type": "user",
  "ref_id": "1",
  "text": "some text",
  "dim": 100
}
```

### 生成并保存向量

`POST /vector/generate`

说明：

- `user` 类型会强制重新计算。
- `survey` 类型会优先复用已有向量。

## 3. 相似度控制

### 标记问卷不再推荐

`POST /similarity/dismiss`

### 按问卷放弃相似度结果

`POST /similarity/abandon`

### 按填写记录放弃相似度结果

`POST /similarity/abandon/{fill_id}`

## 当前行为说明

- 用户完成填写后，相关向量会失效，下一次推荐会重新生成。
- 任务大厅推荐依赖这套内部接口和相似度服务。

## 常见错误码

- `401` 未登录或 Token 过期
- `404` 资源不存在
- `422` 参数校验失败
- `500` 服务器内部错误
