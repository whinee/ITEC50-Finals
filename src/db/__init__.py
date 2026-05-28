"""Database Engine Configuration.

The absolute core of DeciMark's persistence layer. This module boots up both the synchronous SQLAlchemy engine (used exclusively for safe, sequential table creation) and the blazing-fast asynchronous `asyncpg` engine (used for high-concurrency API traffic).
"""
