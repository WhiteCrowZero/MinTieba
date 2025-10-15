# MinTieba
模仿百度贴吧

项目目录结构：
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
│  ├─ gunicorn.log
│  ├─ django.log
│  ├─ error.log
│  └─ access.log
│
└─ static/                     ← 静态文件
   ├─ uploads/
   └─ media/

```
