-- ============================================
-- 第六元素 - 用户画像测试数据
-- 基于Tag系统实现用户画像
-- ============================================

-- 说明：
-- 1. 用户画像通过Tag和UserTag表实现，不使用独立的UserProfile表
-- 2. Tag类型包括：gender, age, grade, college, major, mbti, interest, organization, consumption, career, skill, status
-- 3. 执行前请确保已有core_appuser表和相关数据

-- ============================================
-- 1. 插入测试用户（如果不存在）
-- ============================================

-- 在导入新SQL前执行清理（使用整数ID）
DELETE FROM core_usertag WHERE user_id IN (100, 101, 102);
DELETE FROM core_authtoken WHERE user_id IN (100, 101, 102);
DELETE FROM core_authcredential WHERE user_id IN (100, 101, 102);
DELETE FROM core_appuser WHERE id IN (100, 101, 102);

-- 测试用户1：张三 (ID=100)
INSERT INTO core_appuser (id, nickname, email, credit_score, points, activity_points, status, created_at, updated_at)
VALUES 
(100, '张三', 'zhangsan@example.com', 85, 500, 120, 'normal', NOW(), NOW())
ON DUPLICATE KEY UPDATE nickname = nickname;

-- 张三的密码（密码: 123456）
INSERT INTO core_authcredential (user_id, password_hash, created_at, updated_at)
VALUES (100, 'pbkdf2_sha256$1200000$GtWDvwOA2Ci8NUTmCIEN6y$LrKtyQv43LYic4GY/Y0fv7WkmMdBjDdvDyP02pEzzBU=', NOW(), NOW())
ON DUPLICATE KEY UPDATE password_hash = password_hash;

-- 张三的Token
INSERT INTO core_authtoken (user_id, token, expires_at, created_at)
VALUES (100, 'token_zhangsan_2026_secure', DATE_ADD(NOW(), INTERVAL 30 DAY), NOW());

-- 测试用户2：李四 (ID=101)
INSERT INTO core_appuser (id, nickname, email, credit_score, points, activity_points, status, created_at, updated_at)
VALUES 
(101, '李四', 'lisi@example.com', 92, 1200, 350, 'normal', NOW(), NOW())
ON DUPLICATE KEY UPDATE nickname = nickname;

INSERT INTO core_authcredential (user_id, password_hash, created_at, updated_at)
VALUES (101, 'pbkdf2_sha256$1200000$1liA7ykQMoy6zJF8ViwqDm$G8H0nLqP12hvnTi5T0jZIvk9P7ao4XCBLGoaXyeGg7w=', NOW(), NOW())
ON DUPLICATE KEY UPDATE password_hash = password_hash;

INSERT INTO core_authtoken (user_id, token, expires_at, created_at)
VALUES (101, 'token_lisi_2026_secure', DATE_ADD(NOW(), INTERVAL 30 DAY), NOW());

-- 测试用户3：王五 (ID=102)
INSERT INTO core_appuser (id, nickname, email, credit_score, points, activity_points, status, created_at, updated_at)
VALUES 
(102, '王五', 'wangwu@example.com', 78, 800, 200, 'normal', NOW(), NOW())
ON DUPLICATE KEY UPDATE nickname = nickname;

INSERT INTO core_authcredential (user_id, password_hash, created_at, updated_at)
VALUES (102, 'pbkdf2_sha256$1200000$0EnSJaVIVIBn1s1YGW5ktX$+zlGWyuNwFLu1dAQc3kjBbvgnVHrEuk/aPVX7fUAIpw=', NOW(), NOW())
ON DUPLICATE KEY UPDATE password_hash = password_hash;

INSERT INTO core_authtoken (user_id, token, expires_at, created_at)
VALUES (102, 'token_wangwu_2026_secure', DATE_ADD(NOW(), INTERVAL 30 DAY), NOW());

-- ============================================
-- 2. 插入画像标签（Tag表）
-- ============================================

-- 性别标签
INSERT INTO core_tag (name, type, created_at) VALUES ('男', 'gender', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('女', 'gender', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('保密', 'gender', NOW());

-- 年龄标签
INSERT INTO core_tag (name, type, created_at) VALUES ('18', 'age', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('19', 'age', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('20', 'age', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('21', 'age', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('22', 'age', NOW());

-- 年级标签
INSERT INTO core_tag (name, type, created_at) VALUES ('大一', 'grade', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('大二', 'grade', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('大三', 'grade', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('大四', 'grade', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('研一', 'grade', NOW());

-- 学院标签
INSERT INTO core_tag (name, type, created_at) VALUES ('计算机科学学院', 'college', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('物理学院', 'college', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('经济管理学院', 'college', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('外国语学院', 'college', NOW());

-- 专业标签
INSERT INTO core_tag (name, type, created_at) VALUES ('计算机科学与技术', 'major', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('软件工程', 'major', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('人工智能', 'major', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('应用物理学', 'major', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('工商管理', 'major', NOW());

-- MBTI标签
INSERT INTO core_tag (name, type, created_at) VALUES ('INTJ', 'mbti', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('ENTP', 'mbti', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('INFP', 'mbti', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('ESTJ', 'mbti', NOW());

-- 兴趣标签
INSERT INTO core_tag (name, type, created_at) VALUES ('人工智能', 'interest', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('机器学习', 'interest', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('深度学习', 'interest', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('Web开发', 'interest', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('移动开发', 'interest', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('摄影', 'interest', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('阅读', 'interest', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('运动健身', 'interest', NOW());

-- 组织/社团标签
INSERT INTO core_tag (name, type, created_at) VALUES ('校学生会技术部', 'organization', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('ACM竞赛队', 'organization', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('摄影社', 'organization', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('创业协会', 'organization', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('志愿者协会', 'organization', NOW());

-- 消费偏好标签
INSERT INTO core_tag (name, type, created_at) VALUES ('数码', 'consumption', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('图书', 'consumption', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('游戏', 'consumption', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('奶茶', 'consumption', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('咖啡', 'consumption', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('运动装备', 'consumption', NOW());

-- 职业意向标签
INSERT INTO core_tag (name, type, created_at) VALUES ('大厂', 'career', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('考研', 'career', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('创业', 'career', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('考公', 'career', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('留学', 'career', NOW());

-- 技能标签
INSERT INTO core_tag (name, type, created_at) VALUES ('Python', 'skill', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('Java', 'skill', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('C++', 'skill', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('JavaScript', 'skill', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('算法', 'skill', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('数据分析', 'skill', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('前端开发', 'skill', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('后端开发', 'skill', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('视频剪辑', 'skill', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('平面设计', 'skill', NOW());

-- 当前状态标签
INSERT INTO core_tag (name, type, created_at) VALUES ('正在准备期末考试', 'status', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('寻找实习机会', 'status', NOW());
INSERT INTO core_tag (name, type, created_at) VALUES ('准备考研中', 'status', NOW());

-- ============================================
-- 3. 关联用户与标签（UserTag表）- 张三的完整画像
-- ============================================

-- 张三的基本信息
INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name = '男' AND t.type = 'gender';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name = '20' AND t.type = 'age';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name = '大二' AND t.type = 'grade';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name = '计算机科学学院' AND t.type = 'college';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name = '计算机科学与技术' AND t.type = 'major';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name = 'INTJ' AND t.type = 'mbti';

-- 张三的兴趣（多个）
INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name IN ('人工智能', '机器学习', '深度学习') AND t.type = 'interest';

-- 张三的组织经历（多个）
INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name IN ('校学生会技术部', 'ACM竞赛队') AND t.type = 'organization';

-- 张三的消费偏好
INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name IN ('数码', '图书', '游戏') AND t.type = 'consumption';

-- 张三的职业意向
INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name IN ('大厂', '考研') AND t.type = 'career';

-- 张三的技能
INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name IN ('Python', 'Java', 'C++', '算法') AND t.type = 'skill';

-- 张三的当前状态
INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'zhangsan@example.com' 
  AND t.name = '正在准备期末考试' AND t.type = 'status';

-- ============================================
-- 4. 李四的画像（部分完善）
-- ============================================

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'lisi@example.com' 
  AND t.name = '女' AND t.type = 'gender';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'lisi@example.com' 
  AND t.name = '19' AND t.type = 'age';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'lisi@example.com' 
  AND t.name = '大一' AND t.type = 'grade';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'lisi@example.com' 
  AND t.name = '物理学院' AND t.type = 'college';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'lisi@example.com' 
  AND t.name = '应用物理学' AND t.type = 'major';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'lisi@example.com' 
  AND t.name = 'INFP' AND t.type = 'mbti';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'lisi@example.com' 
  AND t.name IN ('阅读', '摄影') AND t.type = 'interest';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'lisi@example.com' 
  AND t.name IN ('Python', '数据分析') AND t.type = 'skill';

-- ============================================
-- 5. 王五的画像（刚开始填写）
-- ============================================

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'wangwu@example.com' 
  AND t.name = '男' AND t.type = 'gender';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'wangwu@example.com' 
  AND t.name = '21' AND t.type = 'age';

INSERT INTO core_usertag (user_id, tag_id, created_at)
SELECT u.id, t.id, NOW()
FROM core_appuser u, core_tag t
WHERE u.email = 'wangwu@example.com' 
  AND t.name = '大三' AND t.type = 'grade';

-- ============================================
-- 6. 验证查询（测试用）
-- ============================================

-- 查看张三的完整画像
SELECT 
    u.nickname,
    t.type AS tag_type,
    t.name AS tag_name
FROM core_appuser u
JOIN core_usertag ut ON u.id = ut.user_id
JOIN core_tag t ON ut.tag_id = t.id
WHERE u.email = 'zhangsan@example.com'
ORDER BY t.type, t.name;

-- 统计各用户的画像完成度
SELECT 
    u.nickname,
    u.email,
    COUNT(DISTINCT t.type) AS filled_fields_count,
    ROUND(COUNT(DISTINCT t.type) / 12.0 * 100, 0) AS completion_rate
FROM core_appuser u
LEFT JOIN core_usertag ut ON u.id = ut.user_id
LEFT JOIN core_tag t ON ut.tag_id = t.id AND t.type IN ('gender', 'age', 'grade', 'college', 'major', 'mbti', 'interest', 'organization', 'consumption', 'career', 'skill', 'status')
WHERE u.email IN ('zhangsan@example.com', 'lisi@example.com', 'wangwu@example.com')
GROUP BY u.id, u.nickname, u.email
ORDER BY completion_rate DESC;

-- 查找拥有相同学院标签的用户（推荐匹配）
SELECT 
    u.nickname,
    u.email,
    t.name AS college
FROM core_appuser u
JOIN core_usertag ut ON u.id = ut.user_id
JOIN core_tag t ON ut.tag_id = t.id
WHERE t.type = 'college' AND t.name = '计算机科学学院';

COMMIT;
