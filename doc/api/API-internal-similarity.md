# 内部：相似度 / 向量 相关 API（Internal APIs）

说明：以下 API 均为内部接口，仅供服务间或后台调用，需要 `Authorization: Bearer <token>` 鉴权。请勿将这些接口暴露给未经授权的第三方。

1. POST `/api/v1/internal/vector/generate-string`
   - 描述：为给定对象（`user` 或 `survey`）生成用于向量化的一段字符串。
   - 输入 JSON：
     - `ref_type`: `"user"` 或 `"survey"`（必填）
     - `ref_id`: 对象 ID（必填）
   - 返回：`{"text": ""}`（当前实现保留空串，TODO：可改为基于题目/用户资料的拼接文本）
   - 备注：此接口当前为占位，返回空字符串以便上层流程保持一致。

2. POST `/api/v1/internal/vector/generate`
   - 描述：为指定对象生成并持久化向量（若已存在则按规则复用）。
   - 输入 JSON：
     - `ref_type`: `"user"` 或 `"survey"`（必填）
     - `ref_id`: 对象 ID（必填）
     - `dim`: 可选，向量维度，默认 100
   - 行为：
     - 若数据库已有向量：
       - 对于 `user`：若向量的 `created_at` 为当天，直接返回该向量；否则重新生成并覆盖。
       - 对于 `survey`：若已有向量直接返回。
     - 若无向量：调用内部的文本生成（当前返回空字符串）→ 将文本向量化（当前为确定性 placeholder 向量化）→ 存入 `IDVector` 表（以 float32 二进制存储）→ 返回向量数组。
   - 返回：`{"vector": [float,...]}`

3. POST `/api/v1/internal/similarity/compute`
   - 描述：计算并返回指定 `user_id` 与 `survey_id` 的余弦相似度；若当天已有相同配对的记录则直接返回缓存并标记 `cached=true`，否则计算并写入 `SurveyUserSimilarity` 表后返回。
   - 输入 JSON：`{"user_id":"...","survey_id":"..."}`
   - 返回：`{"cosine": float, "cached": bool}` 或 422/错误信息

4. POST `/api/v1/internal/vector/encode`
   - 描述：把给定文本编码为向量并存入 `IDVector`。
   - 输入 JSON：`{"ref_type":"user|survey","ref_id":"...","text":"...","dim":100}`
   - 返回：`{"vector": [float,...]}`
   - 备注：不同于 `/generate`，该接口直接接受任意文本进行编码并持久化。

5. POST `/api/v1/internal/recommend`
   - 描述：为给定 `user_id` 返回若干相似度最高的问卷（内部用于召回/推荐）。
   - 输入 JSON：`{"user_id":"...","num":10}`（`num` 为返回数量）
   - 行为：
     - 从数据库随机抽取 `10 * num` 条问卷（或数据库返回上限），为每个问卷计算与用户的余弦相似度（若已有当天缓存则复用，否则生成问卷向量并计算并持久化相似度）。
     - 将候选按 cosine 降序排序，返回 top `num`。
   - 返回：`{"items": [{"id":"...","title":"...","cosine":float}, ...]}`

安全与性能备注：
- 向量在数据库中以二进制 `float32` 存储（`BinaryField`），读取时会反序列化为浮点数组；当规模或检索需求上升时，建议将向量同步到专用向量库（Milvus / Qdrant / Faiss）并在关系库中只存元数据/外部 id。
- `generate-string` 当前实现返回空字符串；建议改为基于 `Survey.title+description` 或 `AppUser` 的 `nickname+tags` 生成更有意义的文本，以提升向量质量。

---

文档维护：若你希望我把 `generate-string` 改写为基于问卷/用户字段的文本生成，请回复我做哪一项（survey / user / 两者）。
