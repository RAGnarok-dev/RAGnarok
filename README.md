## CI/CD 执行流程

1. 安装uv工具：
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. 提交代码前本地测试：
```bash
uv pip install -e . && pytest
```

3. 推送代码到main分支或创建PR时，GitHub Actions会自动执行：
- 核心模块测试
- 服务端测试
- 工具包测试

4. 确保对`.github/workflows/ci.yml`文件有写入权限
