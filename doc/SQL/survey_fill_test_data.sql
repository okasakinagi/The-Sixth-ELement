-- Survey Fill 测试数据（MySQL）
-- 注意：执行前请确认数据库已建表（Django migrate）
-- 依赖：core_appuser 中存在用户 100/101/102（可先执行 user_profile_test_data.sql）

-- 清理旧数据（避免唯一约束冲突）
UPDATE core_survey SET active_questionnaire_id = NULL WHERE id IN (2001, 2002, 2003, 2004, 2005, 2006, 2007);
DELETE FROM core_answer WHERE response_id IN (6001, 6002, 6003, 6004, 6005);
DELETE FROM core_response WHERE id IN (6001, 6002, 6003, 6004, 6005);
DELETE FROM core_questionoption WHERE id IN (
  5001, 5002, 5003, 5004, 5005, 5006,
  5007, 5008, 5009, 5010, 5011, 5012,
  5013, 5014, 5015
);
DELETE FROM core_question WHERE id IN (4001, 4002, 4003, 4004, 4005, 4006);
DELETE FROM core_questionnaire WHERE id IN (3001, 3004, 3005, 3006, 3007);
DELETE FROM core_surveytag WHERE survey_id IN (2001, 2002, 2003, 2004, 2005, 2006, 2007);
DELETE FROM core_survey WHERE id IN (2001, 2002, 2003, 2004, 2005, 2006, 2007);
DELETE FROM core_notification WHERE id IN (7001, 7002, 7003);
DELETE FROM core_tag WHERE type = 'survey_type' AND name IN ('校园调研', '教学反馈', '就业调研', '健康问卷', '服务反馈');

-- 1) 问卷（Survey）
INSERT INTO core_survey (
  id, owner_id, title, description, estimated_minutes, difficulty, reward_points, publish_cost_points,
  deadline, target, completed, status, active_questionnaire_id, created_at, updated_at
)
VALUES
  (2001, 100, '校园饮食习惯调查', '了解学生饮食习惯与偏好', 5, 2, 5, 5, DATE_ADD(NOW(), INTERVAL 7 DAY), 50, 0, 'published', NULL, NOW(), NOW());

-- 1.2) 额外问卷（用于任务大厅与管理页展示）
INSERT INTO core_survey (
  id, owner_id, title, description, estimated_minutes, difficulty, reward_points, publish_cost_points,
  deadline, target, completed, status, active_questionnaire_id, created_at, updated_at
)
VALUES
  (2002, 100, '课程体验回访', '这学期的主要课程体验', 8, 4, 4, 0, DATE_ADD(NOW(), INTERVAL 14 DAY), 80, 0, 'draft', NULL, NOW(), NOW()),
  (2003, 100, '心理健康与压力', '期末周压力与缓解方式', 9, 5, 5, 0, DATE_ADD(NOW(), INTERVAL 10 DAY), 80, 0, 'paused', NULL, NOW(), NOW()),
  (2004, 100, '实习就业意向', '求职方向、城市与行业偏好', 7, 4, 4, 0, DATE_ADD(NOW(), INTERVAL 5 DAY), 2, 0, 'published', NULL, NOW(), NOW()),
  (2005, 102, '图书馆使用体验', '空间、座位、设备反馈', 4, 2, 2, 0, DATE_ADD(NOW(), INTERVAL 9 DAY), 120, 0, 'published', NULL, NOW(), NOW()),
  (2006, 100, '校园出行与班车', '线路、班次与满意度调查', 4, 2, 2, 0, DATE_ADD(NOW(), INTERVAL 12 DAY), 180, 0, 'published', NULL, NOW(), NOW()),
  (2007, 102, '艺术节节目征集', '报名你想展示的节目', 5, 2, 2, 0, DATE_ADD(NOW(), INTERVAL 11 DAY), 100, 0, 'published', NULL, NOW(), NOW());

-- 2) 问卷版本（Questionnaire）
INSERT INTO core_questionnaire (id, survey_id, version, status, title, created_at, updated_at)
VALUES
  (3001, 2001, 1, 'published', '校园饮食习惯调查', NOW(), NOW());

-- 2.2) 问卷版本（Questionnaire）- 实习就业意向
INSERT INTO core_questionnaire (id, survey_id, version, status, title, created_at, updated_at)
VALUES
  (3004, 2004, 1, 'published', '实习就业意向', NOW(), NOW());

-- 2.3) 问卷版本（Questionnaire）- 图书馆使用体验
INSERT INTO core_questionnaire (id, survey_id, version, status, title, created_at, updated_at)
VALUES
  (3005, 2005, 1, 'published', '图书馆使用体验', NOW(), NOW());

-- 2.4) 问卷版本（Questionnaire）- 校园出行与班车
INSERT INTO core_questionnaire (id, survey_id, version, status, title, created_at, updated_at)
VALUES
  (3006, 2006, 1, 'published', '校园出行与班车', NOW(), NOW());

-- 2.5) 问卷版本（Questionnaire）- 艺术节节目征集
INSERT INTO core_questionnaire (id, survey_id, version, status, title, created_at, updated_at)
VALUES
  (3007, 2007, 1, 'published', '艺术节节目征集', NOW(), NOW());

-- 3) 回填 active_questionnaire_id
UPDATE core_survey SET active_questionnaire_id = 3001 WHERE id = 2001;
UPDATE core_survey SET active_questionnaire_id = 3004 WHERE id = 2004;
UPDATE core_survey SET active_questionnaire_id = 3005 WHERE id = 2005;
UPDATE core_survey SET active_questionnaire_id = 3006 WHERE id = 2006;
UPDATE core_survey SET active_questionnaire_id = 3007 WHERE id = 2007;

-- 4) 题目（Question）
INSERT INTO core_question (id, questionnaire_id, order_no, type, title, description, is_required, config_json, logic_json, created_at, updated_at)
VALUES
  (4001, 3001, 1, 'single', '您最常选择的就餐方式是？', NULL, 1, NULL, NULL, NOW(), NOW()),
  (4002, 3001, 2, 'multi', '您偏好的菜系有哪些？', NULL, 1, NULL, NULL, NOW(), NOW()),
  (4003, 3001, 3, 'text', '请写下您对食堂的建议', NULL, 0, NULL, NULL, NOW(), NOW()),
  (4004, 3005, 1, 'single', '您每周去图书馆的频率是？', NULL, 1, NULL, NULL, NOW(), NOW()),
  (4005, 3006, 1, 'single', '您最常使用的出行方式是？', NULL, 1, NULL, NULL, NOW(), NOW()),
  (4006, 3007, 1, 'text', '请填写你想报名的节目名称', NULL, 1, NULL, NULL, NOW(), NOW());

-- 5) 选项（QuestionOption）
INSERT INTO core_questionoption (id, question_id, order_no, label, value, is_other, extra_config_json, created_at)
VALUES
  (5001, 4001, 1, '食堂', '食堂', 0, NULL, NOW()),
  (5002, 4001, 2, '外卖', '外卖', 0, NULL, NOW()),
  (5003, 4001, 3, '自炊', '自炊', 0, NULL, NOW()),
  (5004, 4002, 1, '川菜', '川菜', 0, NULL, NOW()),
  (5005, 4002, 2, '粤菜', '粤菜', 0, NULL, NOW()),
  (5006, 4002, 3, '西餐', '西餐', 0, NULL, NOW()),
  (5007, 4004, 1, '0-1次', '0-1次', 0, NULL, NOW()),
  (5008, 4004, 2, '2-3次', '2-3次', 0, NULL, NOW()),
  (5009, 4004, 3, '4次及以上', '4次及以上', 0, NULL, NOW()),
  (5010, 4005, 1, '步行', '步行', 0, NULL, NOW()),
  (5011, 4005, 2, '校内班车', '校内班车', 0, NULL, NOW()),
  (5012, 4005, 3, '自行车', '自行车', 0, NULL, NOW()),
  (5013, 4005, 4, '共享单车', '共享单车', 0, NULL, NOW()),
  (5014, 4005, 5, '网约车', '网约车', 0, NULL, NOW()),
  (5015, 4005, 6, '其他', '其他', 1, NULL, NOW());

-- 6) 任务大厅分类标签
INSERT INTO core_tag (name, type, created_at) VALUES
  ('校园调研', 'survey_type', NOW()),
  ('教学反馈', 'survey_type', NOW()),
  ('就业调研', 'survey_type', NOW()),
  ('健康问卷', 'survey_type', NOW()),
  ('服务反馈', 'survey_type', NOW());

-- 7) 关联问卷类型（SurveyTag）
INSERT INTO core_surveytag (survey_id, tag_id, created_at)
SELECT s.id, t.id, NOW()
FROM core_survey s
JOIN core_tag t ON t.type = 'survey_type'
WHERE s.id = 2001 AND t.name = '校园调研';

INSERT INTO core_surveytag (survey_id, tag_id, created_at)
SELECT s.id, t.id, NOW()
FROM core_survey s
JOIN core_tag t ON t.type = 'survey_type'
WHERE s.id = 2002 AND t.name = '教学反馈';

INSERT INTO core_surveytag (survey_id, tag_id, created_at)
SELECT s.id, t.id, NOW()
FROM core_survey s
JOIN core_tag t ON t.type = 'survey_type'
WHERE s.id = 2004 AND t.name = '就业调研';

INSERT INTO core_surveytag (survey_id, tag_id, created_at)
SELECT s.id, t.id, NOW()
FROM core_survey s
JOIN core_tag t ON t.type = 'survey_type'
WHERE s.id = 2003 AND t.name = '健康问卷';

INSERT INTO core_surveytag (survey_id, tag_id, created_at)
SELECT s.id, t.id, NOW()
FROM core_survey s
JOIN core_tag t ON t.type = 'survey_type'
WHERE s.id = 2005 AND t.name = '服务反馈';

INSERT INTO core_surveytag (survey_id, tag_id, created_at)
SELECT s.id, t.id, NOW()
FROM core_survey s
JOIN core_tag t ON t.type = 'survey_type'
WHERE s.id = 2006 AND t.name = '校园调研';

INSERT INTO core_surveytag (survey_id, tag_id, created_at)
SELECT s.id, t.id, NOW()
FROM core_survey s
JOIN core_tag t ON t.type = 'survey_type'
WHERE s.id = 2007 AND t.name = '校园调研';

-- 8) 通知（Task Hall 展示）
INSERT INTO core_notification (id, user_id, type, title, content, status, created_at, read_at)
VALUES
  (7001, 101, 'system', '欢迎来到任务大厅', '已为你推荐最新问卷，快去看看吧！', 'unread', NOW(), NULL),
  (7002, 101, 'system', '问卷更新提醒', '你关注的课程体验回访已更新题目。', 'unread', NOW(), NULL),
  (7003, 101, 'system', '奖励到账', '完成问卷可获得积分奖励。', 'unread', NOW(), NULL);

-- 9) 填写记录（Response）
INSERT INTO core_response (
  id, survey_id, questionnaire_id, user_id, status, started_at, submitted_at, duration_seconds,
  risk_flag, evidence_url, device_fingerprint, ip_hash, created_at, updated_at
)
VALUES
  (6001, 2001, 3001, 101, 'submitted', DATE_SUB(NOW(), INTERVAL 2 HOUR), DATE_SUB(NOW(), INTERVAL 110 MINUTE), 600,
   0, NULL, 'dfp_101_a1', 'iphash_101_a1', NOW(), NOW()),
  (6002, 2001, 3001, 102, 'submitted', DATE_SUB(NOW(), INTERVAL 1 HOUR), DATE_SUB(NOW(), INTERVAL 35 MINUTE), 1500,
   0, NULL, 'dfp_102_b1', 'iphash_102_b1', NOW(), NOW()),
  (6003, 2001, 3001, 100, 'in_progress', DATE_SUB(NOW(), INTERVAL 20 MINUTE), NULL, NULL,
   0, NULL, 'dfp_100_c1', 'iphash_100_c1', NOW(), NOW()),
  (6004, 2004, 3004, 101, 'submitted', DATE_SUB(NOW(), INTERVAL 3 HOUR), DATE_SUB(NOW(), INTERVAL 160 MINUTE), 600,
   0, NULL, 'dfp_101_a2', 'iphash_101_a2', NOW(), NOW()),
  (6005, 2004, 3004, 102, 'submitted', DATE_SUB(NOW(), INTERVAL 2 HOUR), DATE_SUB(NOW(), INTERVAL 90 MINUTE), 900,
   0, NULL, 'dfp_102_b2', 'iphash_102_b2', NOW(), NOW());

-- 10) 答案（Answer）
INSERT INTO core_answer (response_id, question_id, value_text, value_json, created_at, updated_at)
VALUES
  -- 李四（单选：外卖，多选：川菜+西餐，文本建议）
  (6001, 4001, '外卖', NULL, NOW(), NOW()),
  (6001, 4002, NULL, JSON_ARRAY('川菜', '西餐'), NOW(), NOW()),
  (6001, 4003, '食堂多一些清淡和低油选择', NULL, NOW(), NOW()),
  -- 王五（单选：食堂，多选：粤菜，文本建议）
  (6002, 4001, '食堂', NULL, NOW(), NOW()),
  (6002, 4002, NULL, JSON_ARRAY('粤菜'), NOW(), NOW()),
  (6002, 4003, '希望排队更快一些', NULL, NOW(), NOW()),
  -- 张三（进行中，只答了前两题）
  (6003, 4001, '自炊', NULL, NOW(), NOW()),
  (6003, 4002, NULL, JSON_ARRAY('川菜', '粤菜'), NOW(), NOW());
