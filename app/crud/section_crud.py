import json
from slugify import slugify
from typing import Optional, List, Dict, Any
from sqlmodel import select, update
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.section_model import Section
from app.models.user_model import RoleType
from app.core.database.mysql import mysql_manager
from app.core.database.redis import redis_manager
from app.core.logger import logger_manager
from app.core.i18n.i18n import get_message, Language
from app.utils.agent import agent_utils


class SectionCrud:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logger_manager.get_logger(__name__)

    async def _get_section_by_id(self, section_id: int) -> Optional[Section]:
        statement = (
            select(Section)
            .options(joinedload(Section.seo))
            .where(Section.id == section_id, Section.is_active == True)
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def _get_section_by_slug(self, slug: str) -> Optional[Section]:
        statement = (
            select(Section)
            .options(joinedload(Section.seo))
            .where(Section.slug == slug, Section.is_active == True)
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    def _build_section_tree(
        self,
        sections: List[Section],
        language: Language,
        parent_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """构建树形结构的辅助方法"""
        tree = []
        for section in sections:
            if section.parent_id == parent_id:
                children = self._build_section_tree(
                    sections, language, section.id)
                section_dict = {
                    "section_id": section.id,
                    "type": section.type.name,
                    "title": section.chinese_title
                    if language == Language.ZH_CN
                    else section.english_title,
                    "slug": section.slug,
                }
                # 只有当有子节点时才添加 children 字段
                if children:
                    section_dict["children"] = children
                tree.append(section_dict)
        return tree

    async def get_section_lists(self, language: str) -> List[Dict[str, Any]]:
        cache_key = f"section_lists_tree:{language}"
        cache_data = await redis_manager.get_async(cache_key)

        if cache_data:
            return json.loads(cache_data)

        # cache miss, fetch from database
        statement = (
            select(Section)
            .where(Section.is_active == True)
            .order_by(Section.parent_id, Section.id)
        )
        result = await self.db.execute(statement)
        sections = result.scalars().all()

        if not sections:
            raise HTTPException(
                status_code=404,
                detail=get_message(
                    key="section.common.sectionNotFound", lang=language
                ),
            )

        # 构建树形结构
        response = self._build_section_tree(sections, language)

        # 缓存结果
        await redis_manager.set_async(cache_key, json.dumps(response))

        return response

    async def get_section_seo_by_slug(
        self, slug: str, language: Language
    ) -> Optional[Dict[str, Any]]:
        cache_key = f"section_seo_by_slug:{slug}"
        cache_data = await redis_manager.get_async(cache_key)

        if cache_data:
            return json.loads(cache_data)

        section = await self._get_section_by_slug(slug)
        if not section:
            raise HTTPException(
                status_code=404,
                detail=get_message(
                    key="section.common.sectionNotFound",
                    lang=language,
                ),
            )
        if section.seo:
            seo_data = {
                "title": {
                    "zh": section.seo.chinese_title,
                    "en": section.seo.english_title,
                },
                "description": {
                    "zh": section.seo.chinese_description,
                    "en": section.seo.english_description,
                },
                "keywords": {
                    "zh": section.seo.chinese_keywords,
                    "en": section.seo.english_keywords,
                },
            }
            await redis_manager.set_async(cache_key, json.dumps(seo_data))
            return seo_data
        else:
            return None

    async def get_section_details_by_slug(
        self, slug: str, language: Language
    ) -> Optional[Dict[str, Any]]:
        cache_key = f"section_details_by_slug:{slug}:{language}"
        cache_data = await redis_manager.get_async(cache_key)

        if cache_data:
            return json.loads(cache_data)

        section = await self._get_section_by_slug(slug)

        if not section:
            raise HTTPException(
                status_code=404,
                detail=get_message(
                    key="section.common.sectionNotFound", lang=language
                ),
            )

        response = {
            "section_id": section.id,
            "type": section.type.name,
            "slug": section.slug,
            "title": section.chinese_title
            if language == Language.ZH_CN
            else section.english_title,
            "description": section.chinese_description
            if language == Language.ZH_CN
            else section.english_description,
            "parent_id": section.parent_id,
            "created_at": section.created_at.isoformat()
            if section.created_at
            else None,
            "updated_at": section.updated_at.isoformat()
            if section.updated_at
            else None,
        }

        await redis_manager.set_async(cache_key, json.dumps(response))

        return response

    async def update_section(
        self,
        section_id: int,
        language: Language,
        chinese_title: str,
        chinese_description: str,
        role: str,
        seo_id: Optional[int],
        is_active: Optional[bool] = True,
    ) -> bool:
        """Update section"""
        if role != RoleType.admin:
            raise HTTPException(
                status_code=401,
                detail=get_message(
                    key="common.insufficientPermissions", lang=language
                ),
            )

        # 检查是否有section
        section = await self._get_section_by_id(section_id)
        if not section:
            raise HTTPException(
                status_code=404,
                detail=get_message(
                    key="section.common.sectionNotFound", lang=language
                ),
            )

        # 翻译section
        if section.chinese_title != chinese_title:
            english_title = await agent_utils.translate(text=chinese_title)
        else:
            english_title = section.english_title

        if section.chinese_description != chinese_description:
            english_description = await agent_utils.translate(text=chinese_description)
        else:
            english_description = section.english_description

        # 更新slug
        # 生成slug并限制长度
        slug = slugify(english_title, max_length=200)  # 限制在200字符以内，留一些缓冲

        # 更新section
        update_values = {
            "seo_id": seo_id,
            "chinese_title": chinese_title,
            "english_title": english_title,
            "chinese_description": chinese_description,
            "english_description": english_description,
            "slug": slug,
            "is_active": is_active,
        }

        statement = (
            update(Section).where(Section.id ==
                                  section_id).values(**update_values)
        )
        await self.db.execute(statement)
        await self.db.commit()

        # 更新缓存
        await redis_manager.delete_pattern_async(f"section_details:{section_id}:*")
        await redis_manager.delete_pattern_async("section_lists_tree:*")

        return True


def get_section_crud(db: AsyncSession = Depends(mysql_manager.get_db)) -> SectionCrud:
    return SectionCrud(db)
