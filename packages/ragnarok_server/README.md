packages/ragnarok_server/src/ragnarok_server/rdb/models.py中为模型定义文件
在postgre中创建数据库
CREATE DATABASE "RAGnarok";
在(RAGnarok) PS D:\Desktop\university\RAGnarok\packages\ragnarok_server\src\ragnarok_server>
修改模型后需要的指令
alembic revision --autogenerate -m "initial schema"
同步数据库内容所需的指令
alembic upgrade head
进行更新