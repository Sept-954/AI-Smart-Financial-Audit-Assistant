"""Chroma 向量数据库封装——PRD 3.1/4.1。"""

import logging
import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class ChromaIndex:
    """Chroma 向量数据库封装。
    
    PRD 设计要点：
    - 每份财报创建独立 collection：pdf_{sha256前8位}
    - 异常时回退到内存检索
    - 数据持久化在用户本机硬盘
    """
    
    def __init__(self, persist_dir: str = "./chroma_data"):
        self.persist_dir = persist_dir
        self._memory_mode = False
        self._memory_store: list[dict] = []
        
        try:
            os.makedirs(persist_dir, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            logger.info(f"Chroma 初始化成功: {persist_dir}")
        except Exception as e:
            logger.warning(f"Chroma 持久化初始化失败，切换到内存模式: {e}")
            self.client = chromadb.EphemeralClient()
            self._memory_mode = True
    
    def index_report(self, doc_hash: str, chunks: list[dict]) -> Optional[str]:
        """将分片后的文档索引到 Chroma。
        
        参考 Dexter 的 hash 隔离设计。
        PRD 3.1：Chroma collection 以文件 hash 为标识持久化到本地。
        """
        collection_name = f"pdf_{doc_hash[:8]}"
        try:
            # 如果已存在，先删除重建
            try:
                self.client.delete_collection(collection_name)
            except Exception:
                pass
            
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"doc_hash": doc_hash, "type": "financial_report"},
            )
            
            ids = [f"chunk_{i}" for i in range(len(chunks))]
            documents = [c["content"] for c in chunks]
            metadatas = [{
                "start_page": c["start_page"],
                "end_page": c["end_page"],
                "contains_table": c.get("contains_table", False),
            } for c in chunks]
            
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
            )
            
            # 也存一份到内存用于回退
            if self._memory_mode:
                self._memory_store = chunks
            
            logger.info(f"已索引 {len(chunks)} 个片段到 {collection_name}")
            return collection_name
            
        except Exception as e:
            logger.error(f"Chroma 索引失败: {e}")
            # 回退到内存
            self._memory_mode = True
            self._memory_store = chunks
            return None
    
    def search(self, doc_hash: str, query: str, top_k: int = 5) -> dict:
        """在指定文档中搜索相关内容。"""
        collection_name = f"pdf_{doc_hash[:8]}"
        
        try:
            if not self._memory_mode:
                collection = self.client.get_collection(collection_name)
                results = collection.query(
                    query_texts=[query],
                    n_results=top_k,
                )
                return {
                    "documents": results["documents"][0] if results["documents"] else [],
                    "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                    "distances": results["distances"][0] if results["distances"] else [],
                }
            else:
                return self._memory_search(query, top_k)
        except Exception as e:
            logger.warning(f"Chroma 检索失败，使用内存回退: {e}")
            return self._memory_search(query, top_k)
    
    def delete_collection(self, doc_hash: str) -> bool:
        """删除指定文档的 collection。"""
        collection_name = f"pdf_{doc_hash[:8]}"
        try:
            self.client.delete_collection(collection_name)
            return True
        except Exception as e:
            logger.warning(f"删除 collection 失败: {e}")
            return False
    
    def list_collections(self) -> list[dict]:
        """列出所有 collection。"""
        try:
            collections = self.client.list_collections()
            return [{"name": c.name, "count": c.count()} for c in collections]
        except Exception:
            return []
    
    def clear_all(self) -> dict:
        """清除所有数据。PRD 3.1 数据清除机制。"""
        result = {"chroma_cleared": False, "memory_cleared": False, "message": ""}
        try:
            collections = self.client.list_collections()
            for c in collections:
                self.client.delete_collection(c.name)
            result["chroma_cleared"] = True
        except Exception as e:
            result["message"] = f"Chroma 目录不存在或已损坏: {e}"
        
        self._memory_store = []
        self._memory_mode = False
        result["memory_cleared"] = True
        return result
    
    def _memory_search(self, query: str, top_k: int = 5) -> dict:
        """内存模式下的简单关键词搜索回退。"""
        query_lower = query.lower()
        scored = []
        for i, chunk in enumerate(self._memory_store):
            content = chunk["content"].lower()
            # 简单关键词命中计数
            score = sum(1 for word in query_lower.split() if word in content)
            if score > 0:
                scored.append((score, i, chunk))
        
        scored.sort(key=lambda x: -x[0])
        top = scored[:top_k]
        
        return {
            "documents": [t[2]["content"] for t in top],
            "metadatas": [{"start_page": t[2]["start_page"], "end_page": t[2]["end_page"]} for t in top],
            "distances": [1.0 - t[0] / max(len(query_lower.split()), 1) for t in top],
        }
