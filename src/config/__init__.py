"""
Configuration & Environment Engine.

This module forms the immutable configuration backbone of DeciMark. By aggressively parsing both environment variables (`.env`) and static configuration files (`.yml`) into rigidly typed Pydantic models at runtime, this layer ensures absolute environment determinism and eliminates the possibility of hidden configuration faults.
"""
