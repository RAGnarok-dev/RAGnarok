-- 清空表
TRUNCATE TABLE files CASCADE;
TRUNCATE TABLE knowledge_bases CASCADE;
TRUNCATE TABLE tenants CASCADE;
TRUNCATE TABLE embedding_models CASCADE;

-- 重置序列
ALTER SEQUENCE files_id_seq RESTART WITH 1;

-- 首先插入 embedding model
INSERT INTO embedding_models (name, dimension) VALUES
('text-embedding-3-small', 1536),
('text-embedding-3-large', 3072);

-- 插入 tenant
INSERT INTO tenants (name, email, password_hash, is_active) VALUES
('Default Tenant', 'admin@example.com', 'dummy_hash', true);

-- 插入 knowledge base
INSERT INTO knowledge_bases (title, description, embedding_model_id, odb_name, created_by) VALUES
('Default Knowledge Base', 'The default knowledge base for testing', 1, 'default_odb', 'tenant-1'),
('Technical Documentation', 'Technical documentation and guides', 1, 'tech_docs_odb', 'tenant-1'),
('Product Manuals', 'Product user manuals and guides', 1, 'product_manuals_odb', 'tenant-1');

-- 插入根目录文件
INSERT INTO files (name, description, type, size, location, created_by, parent_id, knowledge_base_id) VALUES
('root', 'Root directory', 'root', 0, '/', 'tenant-1', NULL, 1);
