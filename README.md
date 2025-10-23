# MinTieba
> 模仿百度贴吧的练习小项目

## 基本内容概览
### 项目目录结构
```
MinTieba/                       ← 根目录（项目仓库根）
│
├─ manage.py                    ← Django 启动入口
├─ requirements.txt             ← Python 依赖（生产 / 开发分组）
├─ README.md                    ← 项目说明（部署、功能、技术栈）
├─ .env                         ← 环境变量配置（开发模式）
├─ .gitignore
│
├─ config/                      ← Django 项目配置目录（settings、urls、wsgi、asgi）
│  ├─ __init__.py
│  ├─ settings/
│  │   ├─ __init__.py
│  │   ├─ base.py              ← 公共配置
│  │   ├─ dev.py               ← 开发环境配置
│  │   ├─ prod.py              ← 生产环境配置
│  │   ├─ test.py              ← 测试环境配置
│  │
│  ├─ urls.py                  ← 主路由（聚合 apps 内路由）
│  ├─ asgi.py
│  ├─ wsgi.py
│  └─ celery.py                ← （可选）Celery 异步任务配置
│
├─ apps/                       ← 各功能模块（分层管理，遵循领域驱动设计）
│  ├─ __init__.py
│  │
│  ├─ accounts/                ← 用户与权限模块（User + RBAC）
│  │   ├─ __init__.py
│  │   ├─ models.py
│  │   ├─ serializers.py
│  │   ├─ views.py
│  │   ├─ urls.py
│  │   ├─ permissions.py
│  │   ├─ signals.py
│  │   └─ tests/
│  │        └─ test_user_api.py
│  │
│  ├─ forums/                  ← 吧模块（贴吧、分类、成员）
│  │   ├─ models.py
│  │   ├─ serializers.py
│  │   ├─ views.py
│  │   ├─ urls.py
│  │   └─ services/
│  │        ├─ forum_activity_service.py
│  │        └─ forum_statistics.py
│  │
│  ├─ posts/                   ← 帖子与评论模块
│  │   ├─ models.py
│  │   ├─ serializers.py
│  │   ├─ views.py
│  │   ├─ urls.py
│  │   ├─ signals.py
│  │   └─ services/
│  │        └─ post_service.py
│  │
│  ├─ interactions/            ← 点赞、收藏、通知、消息
│  │   ├─ models.py
│  │   ├─ serializers.py
│  │   ├─ views.py
│  │   ├─ urls.py
│  │   └─ tasks.py            ← （可选）异步消息推送任务
│  │
│  ├─ operations/              ← 举报、公告、日志、后台管理
│  │   ├─ models.py
│  │   ├─ views.py
│  │   ├─ serializers.py
│  │   ├─ urls.py
│  │   └─ admin.py
│  │
│  └─ common/                  ← 公共组件与工具
│      ├─ utils/
│      │   ├─ __init__.py
│      │   ├─ cache_utils.py   ← Redis 缓存工具
│      │   ├─ pagination.py    ← 自定义分页器
│      │   ├─ validators.py    ← 通用验证器
│      │   └─ response_wrapper.py ← 标准化API响应
│      │
│      ├─ mixins.py            ← 通用 DRF mixin 类
│      ├─ exceptions.py        ← 全局异常定义
│      ├─ permissions.py       ← 公共权限封装
│      ├─ filters.py           ← 统一筛选器
│      └─ tasks.py             ← 通用异步任务
│
├─ deploy/                     ← 部署与运维目录
│  ├─ docker_env/              ← Docker 运行环境
│  │   ├─ Dockerfile
│  │   ├─ docker-compose.yml
│  │   ├─ nginx/
│  │   │   ├─ nginx.conf
│  │   │   └─ default.conf
│  │   ├─ gunicorn/
│  │   │   ├─ gunicorn.conf.py
│  │   │   └─ start.sh
│  │   ├─ redis/
│  │   │   └─ redis.conf
│  │   ├─ postgres/
│  │   │   └─ init.sql
│  │   └─ supervisor/
│  │       └─ supervisord.conf
│  │
│  ├─ scripts/                 ← 辅助部署脚本
│  │   ├─ init_db.py
│  │   ├─ backup_db.sh
│  │   └─ collect_static.sh
│  │
│  └─ configs/                 ← 环境配置文件模板
│      ├─ .env.dev
│      ├─ .env.prod
│      └─ settings_override.json
│
├─ logs/                       ← 日志文件
│  ├─ django.log
│  ├─ error.log
│  └─ access.log
│
└─ static/                     ← 静态文件
   ├─ uploads/
   └─ media/
```

---

### 数据库设计
- 用户表
  - user_account
    - 用户主信息表
    - 字段：
      - **id(PK)**
      - username
      - password
      - email
      - mobile
      - **role_id(FK role)**
      - avatar_url
      - bio
      - gender
      - is_active
      - is_banned
      - created_at
      - updated_at
  - user_profile
    - 用户扩展信息表
    - 字段：
      - **id(PK)**
      - **user_id(FK user_account)**
      - birthday
      - location
      - signature
      - exp_points
      - level
      - last_login_ip
      - _privacy_settings(ENUM)_
        - public
        - friends
        - private
      - created_at
      - updated_at
  - user_login_history
    - 用户登录记录表
    - 字段：
      - **id(PK)**
      - **user_id(FK user_account)**
      - login_ip
      - device_info
      - login_time
- RBAC表
  - role
    - 角色表
    - 字段：
      - **id(PK)**
      - name
      - description
      - level
  - permission
    - 权限表
    - 字段：
      - **id(PK)**
      - code
      - name
      - description
      - _category_
        - _可设计成外键，此处设计为字段_
  - role_permission_map
    - 角色权限映射表
    - 字段：
      - **id(PK)**
      - **role_id(FK role)**
      - **permission_id(FK permission)**
      - created_at
- 贴吧表
  - forum
    - 吧信息表
    - 字段：
      - **id(PK)**
      - name
      - description
      - cover_image_url
      - **creator_id(FK user_account)**
      - _post_count_
        - 反范式
      - _member_count_
        - 反范式
      - _rules(TEXT)_
      - created_at
      - updated_at
  - forum_category
    - 吧分类表
    - 字段：
      - **id(PK)**
      - name
      - description
      - icon_url
      - sort_order
  - forum_category_map
    - 吧与分类关系表
    - 字段：
      - **id(PK)**
      - **forum_id(FK forum)**
      - **category_id(FK forum_category)**
      - **UNIQUE(forum_id, category_id)**
  - forum_relation
    - 吧关联表
    - 字段
      - **id(PK)**
      - **forum_id(FK forum)**
      - **related_id(FK forum)**
      - **UNIQUE(forum_id, related_id)**
      - created_at
  - forum_member
    - 吧成员表
    - 字段：
      - **id(PK)**
      - **forum_id(FK forum)**
      - **user_id(FK user_account)**
      - **UNIQUE(forum_id, user_id)**
      - _role_type(ENUM)_
        - owner
        - admin
        - member
      - joined_at
      - is_banned
  - forum_activity
    - 吧内活跃度表
    - 字段：
      - **id(PK)**
      - **forum_id(FK forum)**
      - **member_id(FK forum_member)**
      - **UNIQUE(forum_id, member_id)**
      - exp_points
      - level
      - last_active_at
      - sign_in_streak
- 帖子表
  - post
    - 帖子主表
    - 字段：
      - **id(PK)**
      - **forum_id(FK forum)**
      - **author_id(FK user_account)**
      - title
      - content
      - _view_count_
        - 反范式
      - _like_count_
        - 反范式
      - _comment_count_
        - 反范式
      - is_pinned
      - is_locked
      - is_essence
      - is_deleted
      - is_draft
      - scheduled_at
      - created_at
      - updated_at
  - post_image
    - 帖子图片表
    - 字段：
      - **id(PK)**
      - **post_id(FK post)**
      - image_url
      - order_index
      - uploaded_at
  - post_tag
    - 标签定义表
    - 字段：
      - **id(PK)**
      - name
      - description
      - color
  - post_tag_map
    - 帖子标签映射表
    - 字段：
      - **id(PK)**
      - **post_id(FK post)**
      - **tag_id(FK post_tag)**
- 互动表
  - comment
    - 评论表
    - 字段：
      - **id(PK)**
      - **post_id(FK post)**
      - **parent_id(FK comment)**
        - NULL
        - comment_id
      - **author_id(FK user_account)**
      - content
      - _like_count_
        - 反范式
      - floor_number
      - is_deleted
      - created_at
  - like_record
    - 点赞表
    - 字段：
      - **id(PK)**
      - **user_id(FK user_account)**
      - _target_type(ENUM)_
        - post
        - comment
      - **target_id(FK post|comment)**
      - **UNIQUE(user_id, target_type, target_id)**
      - is_active
      - created_at
  - collection_folder
    - 收藏夹表
    - 字段：
      - **id(PK)**
      - **user_id(FK user_account)**
      - name
      - description
      - is_default
      - is_deleted
      - created_at
  - collection_item
    - 收藏内容表
    - 字段：
      - **id(PK)**
      - **user_id(FK user_account)**
      - **folder_id(FK collection_folder)**
      - **post_id(FK post)**
      - **UNIQUE(user_id, folder_id, post_id)**
      - is_deleted
      - created_at
  - user_follow
    - 用户关注表
    - 字段：
      - **id(PK)**
      - **follower_id(FK user_account)**
      - **followed_id(FK user_account)**
      - **UNIQUE(follower_id, followed_id)**
      - created_at
- 消息表
  - notification
    - 通知表
    - 字段：
      - **id(PK)**
      - **user_id(FK user_account)**
      - title
      - message
      - _type(ENUM)_
        - system
        - reply
        - like
        - mention
        - follow
      - _target_type(ENUM)_
        - post
        - comment
      - **target_id(FK post|comment)**
      - is_read
      - created_at
  - message_thread
    - 私信会话表
    - 字段：
      - **id(PK)**
      - **user1_id(FK user_account)**
      - **user2_id(FK user_account)**
      - **UNIQUE(user1_id, user2_id)**
      - last_message_preview
      - updated_at
  - private_message
    - 私信消息表
    - 字段：
      - **id(PK)**
      - **thread_id(FK message_thread)**
      - **sender_id(FK user_account)**
      - content
      - image_url
      - is_read
      - created_at
- 系统表
  - report
    - 举报记录表
    - 字段：
      - **id(PK)**
      - **reporter_id(FK user_account)**
      - **reviewed_by(FK user_account)**
      - target_type
      - target_id
      - _reason(TEXT)_
      - _status(ENUM)_
        - pending
        - approved
        - rejected
      - evidence_url
      - created_at
  - system_log
    - 操作日志表
    - 字段：
      - **id(PK)**
      - **user_id(FK user_account)**
      - _action_type(ENUM)_
        - update
        - create
        - delete
        - select
        - login
        - logout
        - register
        - ban
        - upload
        - recover
        - approve
        - reject
      - _target_type(ENUM)_
        - user
        - forum
        - post
        - comment
      - target_id
      - ip_address
      - created_at
  - announcement
    - 系统公告表
    - 字段：
      - **id(PK)**
      - title
      - content
      - start_time
      - end_time
      - is_active
      - created_at

---

### 第三方库使用
- xxx
