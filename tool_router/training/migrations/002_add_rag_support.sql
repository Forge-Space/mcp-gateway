-- RAG Support Migration
-- Adds vector indexing, caching, and performance tracking for RAG operations
-- Migration: 002_add_rag_support.sql
-- Date: 2025-02-19

-- Enable SQLite extensions for vector operations
-- Note: This requires SQLite with vector extensions or custom implementation

-- Extend knowledge_items table for RAG support
ALTER TABLE knowledge_items ADD COLUMN embedding_vector BLOB;
ALTER TABLE knowledge_items ADD COLUMN retrieval_count INTEGER DEFAULT 0;
ALTER TABLE knowledge_items ADD COLUMN last_accessed TIMESTAMP;
ALTER TABLE knowledge_items ADD COLUMN agent_specific BOOLEAN DEFAULT FALSE;
ALTER TABLE knowledge_items ADD COLUMN agent_types TEXT; -- JSON array of agent types
ALTER TABLE knowledge_items ADD COLUMN source_type TEXT DEFAULT 'manual';
ALTER TABLE knowledge_items ADD COLUMN freshness_score REAL DEFAULT 1.0;

-- Create indexes for new columns
CREATE INDEX idx_knowledge_items_retrieval_count ON knowledge_items(retrieval_count DESC);
CREATE INDEX idx_knowledge_items_last_accessed ON knowledge_items(last_accessed DESC);
CREATE INDEX idx_knowledge_items_agent_specific ON knowledge_items(agent_specific);
CREATE INDEX idx_knowledge_items_freshness_score ON knowledge_items(freshness_score DESC);

-- Vector index table for semantic search
CREATE TABLE vector_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_item_id INTEGER NOT NULL,
    embedding_vector BLOB NOT NULL,
    embedding_model TEXT NOT NULL DEFAULT 'default',
    vector_dimensions INTEGER NOT NULL DEFAULT 768, -- Common dimension for embeddings
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_item_id) REFERENCES knowledge_items(id) ON DELETE CASCADE
);

-- Index for vector lookup performance
CREATE INDEX idx_vector_index_knowledge_item_id ON vector_index(knowledge_item_id);
CREATE INDEX idx_vector_index_created_at ON vector_index(created_at DESC);

-- Query patterns table for intent classification and learning
CREATE TABLE query_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL,
    intent_classification TEXT NOT NULL CHECK (intent_classification IN ('explicit_fact', 'implicit_fact', 'interpretable_rationale', 'hidden_rationale')),
    agent_type TEXT NOT NULL,
    success_rate REAL DEFAULT 0.0,
    usage_count INTEGER DEFAULT 0,
    avg_response_time REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for query patterns
CREATE INDEX idx_query_patterns_agent_type ON query_patterns(agent_type);
CREATE INDEX idx_query_patterns_intent ON query_patterns(intent_classification);
CREATE INDEX idx_query_patterns_success_rate ON query_patterns(success_rate DESC);
CREATE INDEX idx_query_patterns_usage_count ON query_patterns(usage_count DESC);

-- Retrieval cache table (RAGCache-inspired multi-level caching)
CREATE TABLE retrieval_cache (
    cache_key TEXT PRIMARY KEY,
    retrieved_items TEXT NOT NULL, -- JSON array of knowledge item IDs
    query_hash TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hit_count INTEGER DEFAULT 0,
    ttl INTEGER DEFAULT 3600, -- Time to live in seconds (1 hour default)
    cache_level TEXT DEFAULT 'memory' CHECK (cache_level IN ('memory', 'disk', 'database')),
    size_bytes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for cache performance
CREATE INDEX idx_retrieval_cache_timestamp ON retrieval_cache(timestamp DESC);
CREATE INDEX idx_retrieval_cache_cache_level ON retrieval_cache(cache_level);
CREATE INDEX idx_retrieval_cache_hit_count ON retrieval_cache(hit_count DESC);
CREATE INDEX idx_retrieval_cache_ttl ON retrieval_cache(ttl);

-- Agent performance tracking table
CREATE TABLE agent_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_type TEXT NOT NULL,
    query_pattern TEXT NOT NULL,
    retrieval_strategy TEXT NOT NULL,
    performance_metrics TEXT NOT NULL, -- JSON object with detailed metrics
    avg_latency REAL DEFAULT 0.0,
    success_rate REAL DEFAULT 0.0,
    user_satisfaction REAL DEFAULT 0.0,
    knowledge_utilization REAL DEFAULT 0.0,
    cache_hit_rate REAL DEFAULT 0.0,
    relevance_score REAL DEFAULT 0.0,
    total_queries INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance tracking
CREATE INDEX idx_agent_performance_agent_type ON agent_performance(agent_type);
CREATE INDEX idx_agent_performance_avg_latency ON agent_performance(avg_latency);
CREATE INDEX idx_agent_performance_success_rate ON agent_performance(success_rate DESC);
CREATE INDEX idx_agent_performance_updated_at ON agent_performance(updated_at DESC);

-- RAG session tracking for analysis
CREATE TABLE rag_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    agent_type TEXT NOT NULL,
    query TEXT NOT NULL,
    query_analysis TEXT, -- JSON object with query analysis results
    retrieval_results TEXT, -- JSON array of retrieved knowledge items
    context_injection TEXT, -- JSON object with injected context
    final_response TEXT,
    performance_metrics TEXT, -- JSON object with session metrics
    user_feedback TEXT, -- JSON object with user feedback
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes for session tracking
CREATE INDEX idx_rag_sessions_session_id ON rag_sessions(session_id);
CREATE INDEX idx_rag_sessions_agent_type ON rag_sessions(agent_type);
CREATE INDEX idx_rag_sessions_created_at ON rag_sessions(created_at DESC);
CREATE INDEX idx_rag_sessions_completed_at ON rag_sessions(completed_at DESC);

-- Knowledge item relationships for better retrieval
CREATE TABLE knowledge_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_item_id INTEGER NOT NULL,
    target_item_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('related', 'prerequisite', 'alternative', 'example', 'reference')),
    strength REAL DEFAULT 1.0, -- Relationship strength (0.0-1.0)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_item_id) REFERENCES knowledge_items(id) ON DELETE CASCADE,
    FOREIGN KEY (target_item_id) REFERENCES knowledge_items(id) ON DELETE CASCADE
);

-- Indexes for relationships
CREATE INDEX idx_knowledge_relationships_source ON knowledge_relationships(source_item_id);
CREATE INDEX idx_knowledge_relationships_target ON knowledge_relationships(target_item_id);
CREATE INDEX idx_knowledge_relationships_type ON knowledge_relationships(relationship_type);
CREATE INDEX idx_knowledge_relationships_strength ON knowledge_relationships(strength DESC);

-- RAG configuration and settings
CREATE TABLE rag_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    setting_type TEXT NOT NULL CHECK (setting_type IN ('string', 'number', 'boolean', 'json')),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default RAG settings
INSERT INTO rag_settings (setting_key, setting_value, setting_type, description) VALUES
    ('max_context_length', '4000', 'number', 'Maximum context length in tokens'),
    ('default_cache_ttl', '3600', 'number', 'Default cache TTL in seconds'),
    ('min_retrieval_results', '3', 'number', 'Minimum retrieval results'),
    ('max_retrieval_results', '10', 'number', 'Maximum retrieval results'),
    ('similarity_threshold', '0.7', 'number', 'Minimum similarity threshold'),
    ('enable_vector_search', 'true', 'boolean', 'Enable vector search'),
    ('enable_fulltext_search', 'true', 'boolean', 'Enable full-text search'),
    ('enable_caching', 'true', 'boolean', 'Enable multi-level caching'),
    ('cache_memory_limit', '100', 'number', 'Memory cache size limit (MB)'),
    ('performance_tracking', 'true', 'boolean', 'Enable performance tracking'),
    ('auto_optimization', 'true', 'boolean', 'Enable automatic optimization');

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_knowledge_items_timestamp
    AFTER UPDATE ON knowledge_items
BEGIN
    UPDATE knowledge_items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_vector_index_timestamp
    AFTER UPDATE ON vector_index
BEGIN
    UPDATE vector_index SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_query_patterns_timestamp
    AFTER UPDATE ON query_patterns
BEGIN
    UPDATE query_patterns SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_agent_performance_timestamp
    AFTER UPDATE ON agent_performance
BEGIN
    UPDATE agent_performance SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_retrieval_cache_timestamp
    AFTER UPDATE ON retrieval_cache
BEGIN
    UPDATE retrieval_cache SET updated_at = CURRENT_TIMESTAMP WHERE cache_key = NEW.cache_key;
END;

-- Create trigger for automatic retrieval count increment
CREATE TRIGGER increment_retrieval_count
    AFTER UPDATE ON knowledge_items
    WHEN NEW.last_accessed > OLD.last_accessed OR NEW.last_accessed IS NULL
BEGIN
    UPDATE knowledge_items SET retrieval_count = retrieval_count + 1 WHERE id = NEW.id;
END;

-- Create view for RAG performance summary
CREATE VIEW rag_performance_summary AS
SELECT
    agent_type,
    COUNT(*) as total_sessions,
    AVG(avg_latency) as avg_session_latency,
    AVG(success_rate) as avg_success_rate,
    AVG(user_satisfaction) as avg_satisfaction,
    AVG(cache_hit_rate) as avg_cache_hit_rate,
    AVG(relevance_score) as avg_relevance_score,
    SUM(total_queries) as total_queries,
    MAX(updated_at) as last_updated
FROM agent_performance
GROUP BY agent_type;

-- Create view for knowledge base statistics
CREATE VIEW knowledge_base_rag_stats AS
SELECT
    COUNT(*) as total_items,
    COUNT(CASE WHEN embedding_vector IS NOT NULL THEN 1 END) as indexed_items,
    AVG(retrieval_count) as avg_retrieval_count,
    AVG(freshness_score) as avg_freshness,
    COUNT(CASE WHEN agent_specific = TRUE THEN 1 END) as agent_specific_items,
    SUM(retrieval_count) as total_retrievals,
    MAX(updated_at) as last_updated
FROM knowledge_items;

-- Create view for cache performance
CREATE VIEW cache_performance_summary AS
SELECT
    cache_level,
    COUNT(*) as total_entries,
    AVG(hit_count) as avg_hit_count,
    SUM(hit_count) as total_hits,
    AVG(ttl) as avg_ttl,
    COUNT(CASE WHEN timestamp > datetime('now', '-1 hour') THEN 1 END) as recent_entries,
    MAX(updated_at) as last_updated
FROM retrieval_cache
GROUP BY cache_level;

-- Add RLS policies for the new tables (if using Supabase)
-- Note: These would need to be adapted based on your RLS requirements

-- Example RLS policy for knowledge_items (if needed)
-- CREATE POLICY "knowledge_items_rag_policy" ON knowledge_items
-- FOR ALL USING (check_true)
-- WITH CHECK (true);

-- Example RLS policy for agent_performance (if needed)
-- CREATE POLICY "agent_performance_policy" ON agent_performance
-- FOR ALL USING (check_true)
-- WITH CHECK (true);

-- Create indexes for full-text search optimization
-- This would be created after FTS5 setup
-- CREATE VIRTUAL TABLE knowledge_fts USING fts5(content, content='knowledge_items');

-- Comments for migration tracking
-- This migration adds comprehensive RAG support to the existing knowledge base
-- Key features:
-- 1. Vector indexing for semantic search
-- 2. Multi-level caching system
-- 3. Performance tracking and optimization
-- 4. Agent-specific patterns and metrics
-- 5. Query pattern learning and analysis
-- 6. Session tracking for continuous improvement

-- Next migration would add the actual vector search implementation
-- and populate initial data for the RAG system
