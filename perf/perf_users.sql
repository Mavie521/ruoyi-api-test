-- ============================================================
-- 压测账号批量造数：MySQL WHILE 循环 + 整体事务
-- 安全改进：
--   1) 最小权限角色 role_id=100（不再用超级管理员 role_id=1）
--   2) 独立密码 perf12345（不再复用 admin 密码）
-- 支持 200 / 3万 / 10万，改最后一行 CALL 的数字即可
-- 前置：先执行 perf_role_setup.sql 创建角色
-- 用法：mysql -h 127.0.0.1 -P 3307 -uroot -proot ry-vue < perf/perf_users.sql
-- ============================================================

DELIMITER $$

DROP PROCEDURE IF EXISTS gen_perf_users $$

CREATE PROCEDURE gen_perf_users(IN cnt INT)
BEGIN
    DECLARE i INT DEFAULT 1;
    -- 独立压测密码 perf12345 的 bcrypt 哈希（不复用 admin 密码，降低泄露风险）
    DECLARE v_pwd VARCHAR(100) DEFAULT '$2a$10$mJvDkgMS0fy/MoXFPyL0EOLBTiIGoZ9yT16mcnoztqO7c4PoA85pe';

    START TRANSACTION;

    -- 删除策略：先清掉旧账号（幂等，可重复跑）
    DELETE FROM sys_user_role WHERE user_id IN (SELECT user_id FROM sys_user WHERE user_name LIKE 'loaduser_%');
    DELETE FROM sys_user WHERE user_name LIKE 'loaduser_%';

    WHILE i <= cnt DO
        INSERT INTO sys_user (user_name, nick_name, password, status, del_flag)
        VALUES (CONCAT('loaduser_', LPAD(i, 6, '0')),
                CONCAT('压测账号', LPAD(i, 6, '0')),
                v_pwd, '0', '0');
        SET i = i + 1;
    END WHILE;

    -- 挂最小权限压测角色（role_id=100），不再挂超级管理员
    INSERT INTO sys_user_role (user_id, role_id)
    SELECT user_id, 100 FROM sys_user WHERE user_name LIKE 'loaduser_%';

    COMMIT;
END $$

DELIMITER ;

-- 造数（改数字即可扩容：200 / 30000 / 100000）
CALL gen_perf_users(200);
