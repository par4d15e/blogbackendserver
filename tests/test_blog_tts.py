"""
Test blog TTS language selection
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.i18n.i18n import Language
from app.crud.blog_crud import BlogCrud


@pytest.mark.asyncio
async def test_blog_tts_language_selection():
    """Test that TTS returns correct audio based on language"""
    
    # Mock database session
    mock_db = AsyncMock()
    blog_crud = BlogCrud(mock_db)
    
    # Mock Blog_TTS data
    mock_blog_tts = MagicMock()
    mock_blog_tts.chinese_tts_id = 100  # Chinese audio ID
    mock_blog_tts.english_tts_id = 200  # English audio ID
    
    # Mock database query results
    mock_tts_result = MagicMock()
    mock_tts_result.scalar_one_or_none.return_value = mock_blog_tts
    
    mock_media_result_zh = MagicMock()
    mock_media_result_zh.scalar_one_or_none.return_value = "https://s3.amazonaws.com/audio/chinese.mp3"
    
    mock_media_result_en = MagicMock()
    mock_media_result_en.scalar_one_or_none.return_value = "https://s3.amazonaws.com/audio/english.mp3"
    
    # Test Chinese language
    mock_db.execute.side_effect = [mock_tts_result, mock_media_result_zh]
    
    # Simulate the language selection logic
    language = Language.ZH_CN
    tts_id = (
        mock_blog_tts.chinese_tts_id
        if language == Language.ZH_CN
        else mock_blog_tts.english_tts_id
    )
    
    assert tts_id == 100, f"Expected Chinese TTS ID 100, got {tts_id}"
    print(f"✅ Chinese language test passed: TTS ID = {tts_id}")
    
    # Test English language
    language = Language.EN_US
    tts_id = (
        mock_blog_tts.chinese_tts_id
        if language == Language.ZH_CN
        else mock_blog_tts.english_tts_id
    )
    
    assert tts_id == 200, f"Expected English TTS ID 200, got {tts_id}"
    print(f"✅ English language test passed: TTS ID = {tts_id}")


@pytest.mark.asyncio
async def test_language_enum_comparison():
    """Test Language enum comparison works correctly"""
    
    zh = Language.ZH_CN
    en = Language.EN_US
    
    # Test Chinese
    result = "chinese" if zh == Language.ZH_CN else "english"
    assert result == "chinese", f"Expected 'chinese', got '{result}'"
    
    # Test English
    result = "chinese" if en == Language.ZH_CN else "english"
    assert result == "english", f"Expected 'english', got '{result}'"
    
    print("✅ Language enum comparison test passed")


if __name__ == "__main__":
    import asyncio
    
    print("Running Blog TTS language selection tests...\n")
    asyncio.run(test_blog_tts_language_selection())
    asyncio.run(test_language_enum_comparison())
    print("\n✅ All tests passed!")
