-- ============================================================
-- 压测最小权限角色（一次性配置）
-- 作用：压测账号只给最小权限，不再用超级管理员，降低删库/篡改风险
-- 用法：mysql -h 127.0.0.1 -P 3307 -uroot -proot ry-vue < perf/perf_role_setup.sql
-- 注意：先跑这个，再跑 perf_users.sql
-- ============================================================

-- ① 创建压测角色 role_id=100（数据权限=全部数据，否则列表/删除查不到所有用户）
INSERT INTO sys_role (role_id, role_name, role_key, role_sort, data_scope, status, del_flag, create_by, create_time, remark)
VALUES (100, '压测角色', 'perftest', 5, '1', '0', '0', 'admin', NOW(), '压测专用：仅用户/角色查询 + 用户增删')
ON DUPLICATE KEY UPDATE data_scope='1', status='0', del_flag='0', remark='压测专用：仅用户/角色查询 + 用户增删';

-- ② 只分配压测需要的 5 个菜单权限（最小权限）
INSERT IGNORE INTO sys_role_menu (role_id, menu_id)
SELECT 100, menu_id FROM sys_menu
WHERE perms IN ('system:user:list', 'system:user:add', 'system:user:edit', 'system:user:remove', 'system:role:list');
