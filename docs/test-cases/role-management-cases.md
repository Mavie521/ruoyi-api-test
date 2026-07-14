# 角色管理模块 — 测试用例集

## 用例分布

| 级别 | 数量 | 说明 |
|------|------|------|
| P0 | 5 | 核心CRUD |
| P1 | 2 | 状态变更 + 异常 |
| P2 | 3 | 辅助功能 |
| **总计** | **10** | |

---

### TC-Role-01：查询角色列表 P0

| 字段 | 值 |
|------|----|
| 接口 | GET /system/role/list |
| 前置 | 管理员已登录 |
| 请求参数 | pageNum=1, pageSize=10 |
| 预期 | status=200, code=200, rows 不为空, total > 0 |
| 数据库断言 | SELECT COUNT(*) FROM sys_role > 0 |
| 实际结果 | ✅ Pass |

---

### TC-Role-02：获取角色详情 P0

| 字段 | 值 |
|------|----|
| 接口 | GET /system/role/{id} |
| 前置 | 存在角色ID=1 |
| 请求参数 | 无 |
| 预期 | status=200, code=200, data.roleId=1, data.roleName 不为空 |
| 实际结果 | ✅ Pass |

---

### TC-Role-03：新增角色 P0

| 字段 | 值 |
|------|----|
| 接口 | POST /system/role |
| 前置 | 管理员已登录 |
| 请求体 | `{roleName, roleKey, roleSort, status, menuIds: []}` |
| 预期 | status=200, code=200 |
| 数据库断言 | SELECT role_id FROM sys_role WHERE role_key=#{key} 存在 |
| 实际结果 | ✅ Pass |

---

### TC-Role-04：编辑角色 P0

| 字段 | 值 |
|------|----|
| 接口 | PUT /system/role |
| 前置 | 已创建角色 |
| 请求体 | `{roleId, roleName: "新名称", roleKey, roleSort, menuIds: []}` |
| 预期 | status=200, code=200 |
| 数据库断言 | SELECT role_name FROM sys_role WHERE role_id=#{id} = "新名称" |
| 实际结果 | ✅ Pass |

---

### TC-Role-05：删除角色 P0

| 字段 | 值 |
|------|----|
| 接口 | DELETE /system/role/{ids} |
| 前置 | 已创建角色 |
| 请求参数 | role_id 列表 |
| 预期 | status=200, code=200 |
| 数据库断言 | SELECT del_flag FROM sys_role WHERE role_id=#{id} = "2"（逻辑删除） |
| 实际结果 | ✅ Pass |

---

### TC-Role-06：禁用角色 P1

| 字段 | 值 |
|------|----|
| 接口 | PUT /system/role/changeStatus |
| 前置 | 已创建角色 |
| 请求体 | `{roleId, status: "1"}` |
| 预期 | status=200, code=200 |
| 数据库断言 | SELECT status FROM sys_role WHERE role_id=#{id} = "1" |
| 实际结果 | ✅ Pass |

---

### TC-Role-07：缺少必填字段创建角色 P1

| 字段 | 值 |
|------|----|
| 接口 | POST /system/role |
| 前置 | 管理员已登录 |
| 请求体 | `{roleKey, roleSort}`（缺 roleName） |
| 预期 | code != 200（参数校验失败） |
| 实际结果 | ✅ Pass |

---

### TC-Role-08：获取角色下拉选项 P2

| 字段 | 值 |
|------|----|
| 接口 | GET /system/role/optionselect |
| 前置 | 管理员已登录 |
| 预期 | status=200, code=200, data 为列表 |
| 实际结果 | ✅ Pass |

---

### TC-Role-09：获取部门树 P2

| 字段 | 值 |
|------|----|
| 接口 | GET /system/role/deptTree/{id} |
| 前置 | 存在角色ID |
| 预期 | status=200, code=200 |
| 实际结果 | ✅ Pass |

---

### TC-Role-10：授权用户列表 P2

| 字段 | 值 |
|------|----|
| 接口 | GET /system/role/authUser/allocatedList + unallocatedList |
| 前置 | 存在角色ID |
| 预期 | status=200, code=200, 返回分页结构 |
| 实际结果 | ✅ Pass |
