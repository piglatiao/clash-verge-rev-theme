# 贡献新主题 · Contributing a Theme

欢迎提交新主题。本仓库每个主题一个独立文件夹，结构如下：

```
themes/
└── <theme-name>/          # 主题名（英文小写连字符）
    ├── README.md          # 该主题的文档：预览、档位参数、安装、特性
    ├── <theme-name>-*.css # 各档位 CSS
    └── previews/          # 预览截图（档位各一张）
```

要求：

- **单文件自包含 CSS**：壁纸 base64 内嵌，无外链依赖，粘贴即用
- **不使用 `css-xxxxxx` 哈希类名**：客户端升级易失效；请使用官方源码中的稳定类名 + `!important`
- **档位 CSS 命名**：`<theme-name>-<tier>.css`（如 `-high` / `-normal`）
- 根 README 按现有格式加一节主题介绍（预览图 + 「查看主题」链接）
