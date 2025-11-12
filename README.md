# MinTieba

项目接口文档地址：[`MinTieba`](http://124.220.64.116:8000/docs/redoc/)

---

## 项目简介

> 仿百度贴吧的社区后端练习项目

MinTieba 通过实现一个简化版的贴吧社区，覆盖典型社区系统的核心能力：

- 用户体系与 RBAC 权限控制
- 吧管理、分类、成员管理
- 发帖 / 回复 / 点赞 / 收藏 / 私信 等社区交互
- 通知、举报、系统公告等运营能力
- Docker 化部署与基础运维脚本

项目定位为「中小型社区后端服务」的教学与练习项目，重点关注 **架构设计、代码组织与工程实践**，不追求功能完全对标百度贴吧。

---

## 技术栈

- **语言与框架**
    - Python 3.x
    - Django
    - Django REST Framework
    - drf-spectacular（自动生成 OpenAPI / ReDoc 文档）

- **基础设施**
    - MySQL（生产环境）
    - SQLite（开发环境）
    - Redis（缓存 / 消息队列）
    - Celery（异步任务）

> 具体依赖与版本以 `requirements.txt` 和配置文件为准。

---

## 核心功能概览

### 1. 用户与权限（`apps/accounts`）

- 用户注册 / 登录 / 注销
- 用户信息维护（头像、签名、个人简介等）
- _登录历史记录（规划中）_
- _关注 / 粉丝关系（规划中）_
- RBAC 权限模型：
    - 角色（`role`）
    - 权限（`permission`）
    - 角色-权限映射（`role_permission_map`）

### 2. 吧与社区结构（`apps/forums`）

- 吧创建 / 编辑 / 删除（受权限控制）
- 吧分类与多分类绑定
- 吧成员管理（加入 / 退出 / 封禁）
- 吧成员角色：吧主 / 小吧主 / 普通成员
- 吧内活跃度与等级体系（`forum_activity`）

### 3. 帖子与评论（`apps/posts`）_（规划中）_

- 发帖 / 编辑 / 删除
- 置顶 / 精华 / 锁定 / 草稿 / 定时发布
- 帖子图片、标签管理
- 评论 / 楼中楼（`parent_id` 结构）
- 楼层号管理（`floor_number`）

### 4. 互动与通知（`apps/interactions`）_（规划中）_

- 点赞（帖子 / 评论）
- 收藏夹与收藏内容
- 系统通知：
    - 回复提醒
    - 点赞提醒
    - @ 提醒
    - 关注提醒
- 私信会话与私信消息

### 5. 运营与系统（`apps/operations`）_（规划中）_

- 举报处理（帖子 / 评论 / 用户等）
- 系统操作日志（`system_log`）
- 系统公告（`announcement`）

---

## 项目目录结构

```text
MinTieba/                       ← 仓库根目录
│
├─ manage.py                    ← Django 启动入口
├─ requirements.txt             ← Python 依赖
├─ README.md                    ← 项目说明
├─ .gitignore
│
├─ config/                      ← Django 项目配置
│  ├─ __init__.py
│  ├─ settings/
│  │   ├─ __init__.py
│  │   ├─ base.py              ← 公共配置
│  │   ├─ dev.py               ← 开发环境配置
│  │   └─ prod.py              ← 生产环境配置
│  │
│  ├─ urls.py                   ← 主路由（聚合各 app 路由）
│  ├─ asgi.py
│  ├─ wsgi.py
│  └─ celery.py                 ← Celery 配置
│
├─ apps/                        ← 业务模块
│  ├─ __init__.py
│  ├─ accounts/                 ← 用户与权限（User + RBAC）
│  ├─ forums/                   ← 吧、分类、成员
│  ├─ posts/                    ← 帖子与评论
│  ├─ interactions/             ← 点赞、收藏、通知、消息
│  ├─ operations/               ← 举报、公告、日志等运营向能力
│  └─ common/                   ← 公共组件与工具
│      ├─ utils/
│      │   ├─ __init__.py
│      │   ├─ cache_utils.py           ← Redis 缓存工具
│      │   ├─ email_utils.py           ← 邮件发送工具
│      │   ├─ image_utils.py           ← 图像处理工具
│      │   ├─ oss_utils.py             ← 对象存储工具
│      │   ├─ sms_utils.py             ← 短信服务工具
│      │   └─ notification_utils.py    ← 消息通知工具
│      │
│      ├─ auth.py                      ← 用户认证相关封装
│      ├─ delete.py                    ← 软删除相关封装
│      ├─ response_render.py           ← 统一 API 响应格式
│      ├─ exceptions.py                ← 全局异常定义
│      ├─ permissions.py               ← 公共权限封装
│      └─ tasks.py                     ← 通用异步任务
│
├─ deploy/                      ← 部署与运维
│  ├─ docker_env/               ← Docker 运行环境
│  │   ├─ initdb/
│  │   │   └─ 001_init.sql
│  │   ├─ .env
│  │   ├─ Dockerfile
│  │   └─ docker-compose.yml
│  │
│  └─ scripts/                  ← 部署辅助脚本
│      └─ entrypoint.sh
│
├─ logs/                        ← 日志文件
│  ├─ django.log
│  ├─ error.log
│  └─ access.log
│
└─ static/                      ← 静态与上传文件
   ├─ uploads/
   └─ media/
````

---

## 数据库设计

~~初版设计见[初版数据库设计](https://github.com/MinTieba/MinTieba/blob/main/docs/database_design.md)~~

> 下述为各模块的实体关系图，实际表结构以 Django Models 与迁移文件为准。

* accounts 模块
  ![accounts](https://github.com/WhiteCrowZero/MinTieba/blob/main/docs/imgs/accounts.svg)

* forums 模块
  ![forums](https://github.com/WhiteCrowZero/MinTieba/blob/main/docs/imgs/forums.svg)

* interactions 模块
  ![interactions](https://github.com/WhiteCrowZero/MinTieba/blob/main/docs/imgs/interactions.svg)

* posts 模块
  ![posts](https://github.com/WhiteCrowZero/MinTieba/blob/main/docs/imgs/posts.svg)

* operations 模块
  ![operations](https://github.com/WhiteCrowZero/MinTieba/blob/main/docs/imgs/operations.svg)

---

## 快速开始

### 开发环境

1. 克隆项目

   ```bash
   git clone https://github.com/MinTieba/MinTieba.git
   cd MinTieba
   ```

2. 创建虚拟环境并安装依赖

   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS / Linux:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```

3. 初始化数据库

   开发环境默认可使用 SQLite，如需切换到 MySQL，请在 `config/settings/dev.py` 中调整数据库配置。

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. 启动开发服务器

   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

访问入口：

* 接口文档：`http://127.0.0.1:8000/docs/redoc/`
* 管理后台：`http://127.0.0.1:8000/admin/`

---

### Docker 部署

项目提供基于 Docker 的一键部署方案，相关文件位于 `deploy/docker_env/` 目录。

1. 配置环境变量

   根据实际情况修改：

    * `deploy/docker_env/.env`
    * 数据库密码、Redis 地址、对象存储配置（如 Minio）等敏感信息

2. 构建并启动服务

   在 `deploy/docker_env/` 目录下执行：

   ```bash
   docker-compose up -d --build
   ```

   默认启动组件包括：

    * Web 服务（Django）
    * 数据库（如 MySQL）
    * Redis
    * Minio（对象存储，如有配置）
    * Celery Worker / Beat（如在 `docker-compose.yml` 中开启）

---

> 说明：本项目主要用于个人学习与技术实践，功能与实现将根据实际学习进度持续迭代。




