# 数据库迁移流程图

## Run Database Migration 完整流程

```mermaid
flowchart TD
    Start([开始: Run Database Migration]) --> Wait[等待 5 秒]
    Wait --> CheckAlembic{检查 alembic.ini<br/>是否存在?}
    
    CheckAlembic -->|不存在| Error1[❌ 退出: alembic.ini not found]
    CheckAlembic -->|存在| CheckFiles[检查迁移文件数量<br/>MIGRATION_FILES]
    
    CheckFiles --> CheckDB[检查数据库状态<br/>alembic current]
    CheckDB --> GetVersion[提取数据库当前版本<br/>DB_CURRENT_VERSION]
    CheckDB --> CheckInit{数据库是否<br/>已初始化?}
    
    CheckInit -->|未初始化| CheckFilesCount{迁移文件<br/>数量 = 0?}
    CheckInit -->|已初始化| CheckFilesCount2{迁移文件<br/>数量 = 0?}
    
    %% 场景1: 新部署
    CheckFilesCount -->|是| Scenario1[场景1: 新部署<br/>无迁移文件 + 数据库未初始化]
    Scenario1 --> GenMigration[📝 生成初始迁移<br/>alembic revision --autogenerate]
    GenMigration --> SetPerms[设置文件权限]
    SetPerms --> RunMigration
    
    %% 场景2: 数据库有版本但缺少迁移文件
    CheckFilesCount2 -->|是| Scenario2[场景2: 异常情况<br/>数据库已初始化 + 无迁移文件]
    Scenario2 --> ShowError2[⚠️ 显示错误信息<br/>- 数据库版本<br/>- 缺少迁移文件原因]
    ShowError2 --> Error2[❌ 退出: Cannot proceed]
    
    %% 场景3: 有迁移文件
    CheckFilesCount -->|否| Scenario3[场景3: 有迁移文件]
    CheckFilesCount2 -->|否| Scenario3
    
    Scenario3 --> CheckInit2{数据库是否<br/>已初始化?}
    
    CheckInit2 -->|未初始化| RunMigration
    CheckInit2 -->|已初始化| VersionCheck[📋 检查版本一致性]
    
    VersionCheck --> GetTarget[获取目标版本<br/>alembic heads]
    GetTarget --> CompareVersions{当前版本 =<br/>目标版本?}
    
    CompareVersions -->|是| AlreadyUpToDate[✅ 数据库已是最新版本]
    CompareVersions -->|否| ShowUpgrade[⬆️ 显示升级信息<br/>从 X 升级到 Y]
    CompareVersions -->|无法确定| ProceedAnyway[⚠️ 无法确定版本<br/>继续执行]
    
    AlreadyUpToDate --> RunMigration
    ShowUpgrade --> RunMigration
    ProceedAnyway --> RunMigration
    
    %% 执行迁移（带重试）
    RunMigration[执行迁移<br/>alembic upgrade head] --> CheckSuccess{迁移<br/>成功?}
    
    CheckSuccess -->|成功| CheckOutput{输出包含<br/>Running upgrade?}
    CheckOutput -->|是| ShowUpgradeOutput[显示升级输出]
    CheckOutput -->|否| ShowUpToDate[✅ Database is up to date]
    ShowUpgradeOutput --> Success
    ShowUpgradeOutput --> Success
    
    CheckSuccess -->|失败| CheckVersionError{是版本<br/>不匹配错误?}
    
    CheckVersionError -->|是| VersionMismatch[❌ 版本不匹配错误]
    VersionMismatch --> ShowVersionError[显示详细错误信息:<br/>- Can't locate revision<br/>- Multiple heads<br/>- target database not up to date]
    ShowVersionError --> ShowReasons[说明可能原因:<br/>- 数据库版本不在迁移链中<br/>- 迁移文件不完整<br/>- 使用了不同的迁移文件]
    ShowReasons --> Error3[❌ 立即退出]
    
    CheckVersionError -->|否| CheckRetry{重试次数<br/>< 3?}
    
    CheckRetry -->|是| WaitRetry[等待 5 秒]
    WaitRetry --> Retry[重试迁移]
    Retry --> RunMigration
    
    CheckRetry -->|否| MaxRetries[❌ 达到最大重试次数]
    MaxRetries --> ShowDebug[显示调试信息:<br/>- 迁移输出<br/>- 当前版本<br/>- 容器日志]
    ShowDebug --> Error4[❌ 退出: Migration failed]
    
    Success([✅ Migration completed])
    
    style Start fill:#e1f5ff
    style Success fill:#d4edda
    style Error1 fill:#f8d7da
    style Error2 fill:#f8d7da
    style Error3 fill:#f8d7da
    style Error4 fill:#f8d7da
    style Scenario1 fill:#fff3cd
    style Scenario2 fill:#f8d7da
    style Scenario3 fill:#d1ecf1
    style VersionMismatch fill:#f8d7da
```

## 场景说明

### 场景1: 新部署
- **条件**: 无迁移文件 + 数据库未初始化
- **操作**: 自动生成初始迁移
- **结果**: 创建第一个迁移文件并应用到数据库

### 场景2: 异常情况
- **条件**: 数据库已初始化 + 无迁移文件
- **操作**: 报错退出
- **原因**: 迁移文件未从代码仓库部署

### 场景3: 正常迁移
- **条件**: 有迁移文件
- **子场景**:
  - **3.1**: 数据库未初始化 → 直接执行迁移
  - **3.2**: 数据库已初始化 → 检查版本一致性后执行迁移
    - 版本相同 → 跳过（已是最新）
    - 版本不同 → 执行升级
    - 版本不匹配 → 报错退出

## 错误处理

### 版本不匹配错误
检测以下 Alembic 错误：
- `Can't locate revision` - 数据库版本不在迁移链中
- `Multiple heads` - 迁移文件有多个头
- `target database is not up to date` - 其他版本问题

### 重试机制
- 最多重试 3 次
- 每次失败后等待 5 秒
- 第 3 次失败后显示详细调试信息并退出

