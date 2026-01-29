-- Survey Fill 测试数据
-- 注意：执行前请确认数据库已建表（Django migrate）

-- 1) 问卷（Survey）
INSERT INTO core_survey (
  id, owner_id, title, description, estimated_minutes, difficulty, reward_points, publish_cost_points,
  deadline, target, completed, status, active_questionnaire_id, created_at, updated_at
)
VALUES
  (2001, 100, '校园饮食习惯调查', '了解学生饮食习惯与偏好', 5, 2, 5, 5, DATE_ADD(NOW(), INTERVAL 7 DAY), 50, 0, 'published', NULL, NOW(), NOW());

-- 2) 问卷版本（Questionnaire）
INSERT INTO core_questionnaire (id, survey_id, version, status, title, created_at, updated_at)
VALUES
  (3001, 2001, 1, 'published', '校园饮食习惯调查', NOW(), NOW());

-- 3) 回填 active_questionnaire_id
UPDATE core_survey SET active_questionnaire_id = 3001 WHERE id = 2001;

-- 4) 题目（Question）
INSERT INTO core_question (id, questionnaire_id, order_no, type, title, description, is_required, config_json, logic_json, created_at, updated_at)
VALUES
  (4001, 3001, 1, 'single', '您最常选择的就餐方式是？', NULL, 1, NULL, NULL, NOW(), NOW()),
  (4002, 3001, 2, 'multi', '您偏好的菜系有哪些？', NULL, 1, NULL, NULL, NOW(), NOW()),
  (4003, 3001, 3, 'text', '请写下您对食堂的建议', NULL, 0, NULL, NULL, NOW(), NOW());

-- 5) 选项（QuestionOption）
INSERT INTO core_questionoption (id, question_id, order_no, label, value, is_other, extra_config_json, created_at)
VALUES
  (5001, 4001, 1, '食堂', '食堂', 0, NULL, NOW()),
  (5002, 4001, 2, '外卖', '外卖', 0, NULL, NOW()),
  (5003, 4001, 3, '自炊', '自炊', 0, NULL, NOW()),
  (5004, 4002, 1, '川菜', '川菜', 0, NULL, NOW()),
  (5005, 4002, 2, '粤菜', '粤菜', 0, NULL, NOW()),
  (5006, 4002, 3, '西餐', '西餐', 0, NULL, NOW());
