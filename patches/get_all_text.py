"""
scrapling 包的补丁模块
补丁 scrapling.parser 模块中 get_all_text 函数，支持增强的 ignore_tags 参数。
"""

# 标准库导入
from typing import Optional, Tuple, Union, List, Set, Iterable, Any

# 本地导入
from scraper.utils.logger import get_logger
logger = get_logger("patches", level="INFO")


# 默认忽略的标签和选择器
DEFAULT_IGNORE_TAGS = (
    # 脚本和样式
    'script', 'style', 'noscript',
)

# Tag 白名单 - 分为简单标签和CSS选择器
WHITELIST_SIMPLE_TAGS = ('html', 'body')  # 简单标签名
WHITELIST_CSS_SELECTORS = ('.post-header', '.post-footer')  # CSS选择器


class ElementMatcher:
    """
    元素匹配器，用于判断元素是否匹配给定的选择器
    """
    def __init__(self, ignore_tags: Iterable[str]):
        """
        初始化匹配器
        
        :param ignore_tags: 要忽略的标签和选择器列表
        """
        self.simple_tags: Set[str] = set()  # 简单标签名
        self.css_selectors: List[str] = []  # CSS 选择器
        self._adaptor = None  # 延迟初始化的 Adaptor 实例
        
        for tag in ignore_tags:
            if not tag or not isinstance(tag, str):
                continue
                
            # 简单标签名
            if tag.isalnum():
                self.simple_tags.add(tag.lower())
            # CSS 选择器
            else:
                self.css_selectors.append(tag)


def _process_node_text(node: Any, strip: bool, valid_values: bool) -> List[str]:
    """
    处理节点的文本内容
    
    :param node: DOM节点
    :param strip: 是否去除文本两端的空白字符
    :param valid_values: 是否只返回非空文本
    :return: 提取的文本列表
    """
    result = []
    
    # 处理节点的文本
    if node.text and isinstance(node.text, str):
        text = node.text.strip() if strip else node.text
        if text and (not valid_values or text.strip()):
            result.append(text)
            
    # 处理尾部文本
    if node.tail and isinstance(node.tail, str):
        tail = node.tail.strip() if strip else node.tail
        if tail and (not valid_values or tail.strip()):
            result.append(tail)
            
    return result


def _is_whitelisted_tag(tag_name: str) -> bool:
    """
    检查标签名是否在白名单中
    
    :param tag_name: 标签名
    :return: 如果在白名单中返回True，否则返回False
    """
    return tag_name.lower() in WHITELIST_SIMPLE_TAGS


def _process_css_selectors(root: Any, css_selectors: List[str]) -> Set[Any]:
    """
    处理CSS选择器并返回匹配的节点集合
    
    :param root: 根节点
    :param css_selectors: CSS选择器列表
    :return: 需要忽略的节点集合
    """
    ignored_nodes = set()
    processed_selectors = set()  # 记录已处理的选择器
    
    for selector in css_selectors:
        # 避免重复处理相似选择器
        selector_key = selector.lower()
        if selector_key in processed_selectors:
            continue
            
        try:
            # 找出所有匹配选择器的节点
            nodes = root.cssselect(selector)
            if not nodes:
                continue
                
            matched_count = len(nodes)
            logger.debug(f"选择器 '{selector}' 匹配了 {matched_count} 个节点，这些节点及其子节点将被忽略")
            processed_selectors.add(selector_key)  # 标记为已处理
            
            # 将匹配的节点及其所有子节点加入忽略集合
            for node in nodes:
                _add_node_to_ignored_set(node, ignored_nodes)
        except Exception as e:
            logger.warning(f"CSS 选择器 '{selector}' 处理失败: {e}")
    
    return ignored_nodes


def _add_node_to_ignored_set(node: Any, ignored_nodes: Set[Any]) -> None:
    """
    将节点及其子节点添加到忽略集合中
    
    :param node: 要忽略的节点
    :param ignored_nodes: 忽略节点的集合
    """
    # 输出详细匹配信息用于调试
    node_desc = getattr(node, 'tag', '')
    if _is_whitelisted_tag(node_desc):
        logger.debug(f"  - 跳过忽略 {node_desc} 标签，避免忽略整个文档")
        return

    class_attr = node.get('class', '')
    if class_attr:
        class_list = class_attr.split()
        # 移除选择器中的点号前缀再比较
        if any(selector.lstrip('.') in class_list for selector in WHITELIST_CSS_SELECTORS):
            logger.debug(f"  - 跳过忽略 {node_desc} 标签")
            return    

    id_attr = node.get('id', '')
    logger.debug(f"  - 匹配节点: <{node_desc} class='{class_attr}' id='{id_attr}'>")

    # 添加节点及其所有子节点到忽略集合
    ignored_nodes.add(node)
    for child in node.xpath('.//*'):
        ignored_nodes.add(child)


def _process_simple_tags(root: Any, simple_tags: Set[str]) -> Set[Any]:
    """
    处理简单标签并返回匹配的节点集合
    
    :param root: 根节点
    :param simple_tags: 简单标签集合
    :return: 需要忽略的节点集合
    """
    ignored_nodes = set()
    
    for node in root.xpath('.//*'):
        tag_name = getattr(node, 'tag', '')
        if tag_name and tag_name.lower() in simple_tags:
            # 特殊处理白名单标签，不忽略它们
            if _is_whitelisted_tag(tag_name):
                logger.debug(f"  - 简单标签匹配：跳过忽略 {tag_name} 标签，避免忽略整个文档")
                continue
            
            # 忽略此节点及其所有子节点
            _add_node_to_ignored_set(node, ignored_nodes)
    
    return ignored_nodes


def patched_get_all_text(
    self: Any,
    separator: str = "\n",
    strip: bool = False,
    ignore_tags: Optional[Union[Tuple[str, ...], List[str]]] = None,
    valid_values: bool = True
) -> Any:
    """
    修改后的 get_all_text 函数，支持更强大的 ignore_tags 参数，包括 CSS 选择器
    
    :param self: Adaptor实例
    :param separator: 用于连接文本的分隔符，默认为换行符
    :param strip: 是否去除文本两端的空白字符
    :param ignore_tags: 要忽略的标签名或CSS选择器列表，为 None 时使用默认值
    :param valid_values: 是否只返回非空文本
    :return: TextHandler 对象
    :raises: 可能抛出 lxml 相关的解析异常
    """
    # 处理 ignore_tags 参数
    if ignore_tags is None:
        ignore_tags = DEFAULT_IGNORE_TAGS
    elif isinstance(ignore_tags, list):
        ignore_tags = tuple(ignore_tags)
    
    if not isinstance(ignore_tags, (tuple, list)):
        raise TypeError(f"ignore_tags 必须是元组或列表，而不是 {type(ignore_tags).__name__}")
    
    # 创建元素匹配器
    matcher = ElementMatcher(ignore_tags)
    self.css_selectors = matcher.css_selectors  # 添加实例属性以便在内部使用
    self.simple_tags = matcher.simple_tags  # 添加实例属性以便在内部使用
    _all_strings: List[str] = []

    try:
        # 处理 CSS 选择器，获取需要忽略的节点
        ignored_nodes = _process_css_selectors(self._root, self.css_selectors)
        
        # 处理简单标签，添加到忽略节点集合
        simple_tag_nodes = _process_simple_tags(self._root, self.simple_tags)
        ignored_nodes.update(simple_tag_nodes)
        
        # 获取所有文本节点，排除被忽略的节点
        for node in self._root.xpath('.//*'):
            # 检查节点是否在忽略集合中
            if node in ignored_nodes:
                continue
            
            # 处理节点文本
            node_texts = _process_node_text(node, strip, valid_values)
            _all_strings.extend(node_texts)
            # 添加空格
            _all_strings.append(' ')
        
        # 处理根元素的文本
        root_texts = _process_node_text(self._root, strip, valid_values)
        if root_texts:
            _all_strings = root_texts + _all_strings
        
        # 返回处理后的文本
        from scrapling.core.custom_types import TextHandler
        return TextHandler(separator.join(_all_strings))
            
    except Exception as e:
        logger.error(f"提取文本时发生错误: {e}", exc_info=True)
        # 发生错误时回退到原始实现
        import scrapling.parser
        return scrapling.parser._original_get_all_text(
            self, separator, strip, ignore_tags, valid_values
        )
