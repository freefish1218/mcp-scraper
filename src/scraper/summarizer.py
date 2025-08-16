"""
文章内容总结模块
使用 LLM 处理文章数据，提取来源和生成关键事实
"""

from typing import List
from pydantic import BaseModel, Field

from scraper.llm_util import get_llm, parse_json
from scraper.models import ScrapedArticle
from scraper.utils import get_logger

logger = get_logger(__name__)


class ArticleSummary(BaseModel):
    """LLM 返回的文章摘要结果模型"""
    source: str = Field(default="", description="文章来源")
    summary: List[str] = Field(default_factory=list, description="关键事实")


async def summarize_article(
    article: ScrapedArticle, 
    content_limit: int = 5000,
    temperature: float = 0,
) -> ScrapedArticle:
    """
    使用 LLM 对文章进行总结，提取来源和生成关键事实
    
    Args:
        article: 需要处理的文章对象
        content_limit: 文章内容的限制长度，默认为5000
        
    Returns:
        ScrapedArticle: 更新后的文章对象，包含来源和关键事实
    """
    # 如果文章没有内容或标题，直接返回原始文章
    if not article.content or not article.title:
        logger.warning(f"文章缺少内容或标题，跳过总结: {article.url}")
        return article
    
    # 获取 LLM 实例
    llm = await get_llm(agent_name=None)
    
    try:
        prompt = get_prompt(article, content_limit)

        # 调用 LLM 获取分析结果
        response = await llm.ainvoke(prompt, temperature=temperature)
        result_text = response.content

        json_text = parse_json(result_text)
        
        try:
            # 使用 Pydantic 验证和解析结果
            result = ArticleSummary.model_validate(json_text)
            
            # 更新文章对象
            if result.source:
                article.source = result.source
            
            if result.summary:
                article.summary = result.summary
        except Exception as e:
            logger.error(f"Pydantic 解析 LLM 结果失败: {e}")
        
        logger.info(f"文章总结完成: {article.url}")
        
    except Exception as e:
        logger.error(f"总结文章时发生错误: {e}")
    
    return article

async def summarize_articles(articles: list[ScrapedArticle]) -> list[ScrapedArticle]:
    """
    批量处理多篇文章，提取来源和生成关键事实
    
    Args:
        articles: 需要处理的文章列表
        
    Returns:
        list[ScrapedArticle]: 更新后的文章列表
    """
    updated_articles = []
    
    for article in articles:
        updated_article = await summarize_article(article)
        updated_articles.append(updated_article)
    
    logger.info(f"批量总结完成，共处理 {len(updated_articles)} 篇文章")
    return updated_articles


def get_prompt(article: ScrapedArticle, content_limit: int = 5000) -> str:
    """
    获取文章总结的提示词
    """

    return f"""
你是信息提取顶尖专家，请分析以下文章，提取文章的关键事实/观点，以及来源。

URL: {article.url}
标题: {article.title}

内容:
{article.content[:content_limit]}

请以 JSON 格式返回结果，只包含 summary 和 source 键:
```json
{{
    "summary": "文章中的关键事实/观点（不得遗漏），以列表形式返回"
    "source": "文章的来源，如媒体名称、作者等，若无法确定，返回空字符串",
}}
```
"""
