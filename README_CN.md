# KnowledgeMiner 2.0

一个用于将原始 Markdown 文档转换为结构化知识库的综合系统，具备自动概念提取、分类、关系映射和智能知识发现功能。

## 🎯 项目概述

KnowledgeMiner 2.0 是一个智能知识挖掘系统，具有模块化架构、增强的数据模型、大语言模型集成和语义搜索功能。Phase 1 建立了具有可插拔组件的坚实基础，而 Phase 2 添加了高级知识发现和洞察生成功能。

## ✨ 功能特性

### 核心功能
- **文档分析**：解析和结构化包含 frontmatter 的 Markdown 文档
- **概念提取**：自动从内容中识别和提取关键概念
- **智能索引**：按类别和关系组织文档
- **内容生成**：从提取的概念生成摘要、文章和反向链接
- **交互式审查**：交互式审查和确认提取的概念
- **灵活配置**：广泛的自定义配置选项
- **错误处理**：整个管道中强大的错误处理和日志记录

### Phase 1 增强功能
- **增强的数据模型**：具有更好类型安全性和验证的新核心模型
- **LLM 集成**：支持 OpenAI、Anthropic Claude 和本地模型（Ollama）
- **嵌入生成**：为概念和文档自动生成语义嵌入
- **状态管理**：用于增量编译的持久化状态跟踪
- **模块化架构**：具有清晰接口的可插拔组件
- **性能提升**：82% 的测试覆盖率和优化的处理管道

### Phase 2：知识发现引擎（新增！）
- **智能关系挖掘**：发现显式、隐式、统计和语义关系
- **模式检测**：识别时间、因果、进化和冲突模式
- **差距分析**：在知识库中查找缺失的概念、关系和证据
- **洞察生成**：生成具有显著性评分的可操作洞察
- **交互式探索**：使用自然语言查询知识库
- **全面测试**：117 个测试，完全覆盖发现功能

### Phase 2：代码审查与安全改进（2025年4月）
- **安全加固**：消除路径遍历漏洞，实现 API 密钥保护
- **性能优化**：文件 I/O 减少 50%，O(n²) → O(n) 算法改进
- **架构增强**：依赖注入模式以获得更好的可测试性
- **缓存优化**：使用 OrderedDict 实现正确的 LRU 缓存
- **全面验证**：6 个验证测试，所有修复 100% 通过

## 安装

### 前置要求

- Python 3.8 或更高版本
- pip 包管理器

### 标准安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/knowledge_compiler.git
cd knowledge_compiler

# 安装依赖
pip install -r requirements.txt
```

### Phase 2 依赖

对于 Phase 2 功能（知识发现引擎）：

```bash
# 安装 Phase 2 依赖
pip install -r requirements.txt

# Phase 2 需要额外的依赖：
# - scikit-learn：统计分析和聚类
# - networkx：关系挖掘的图算法
# - pydantic-settings：增强的配置管理

# 这些已包含在 requirements.txt 中
```

### Phase 1 依赖

对于 Phase 1 功能（LLM 集成、嵌入）：

```bash
# 安装 Phase 1 依赖
pip install -r requirements.txt

# 可选：针对特定的 LLM 提供商
pip install openai anthropic
pip install ollama  # 用于本地模型
```

### 开发环境安装

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 以可编辑模式安装
pip install -e .
```

## 快速开始

### 命令行使用（Phase 1 增强版）

```bash
# 基本使用
python -m src.main_cli --source ./docs --output ./knowledge_base

# 使用 LLM 集成
python -m src.main_cli --source ./docs --output ./knowledge_base --llm-provider openai --model gpt-4

# 启用嵌入生成
python -m src.main_cli --source ./docs --output ./knowledge_base --enable-embeddings

# 使用状态管理（增量编译）
python -m src.main_cli --source ./docs --output ./knowledge_base --state-file state.json

# 详细输出
python -m src.main_cli --source ./docs --output ./knowledge_base --verbose

# 静默模式
python -m src.main_cli --source ./docs --output ./knowledge_base --quiet

# 非交互模式
python -m src.main_cli --source ./docs --output ./knowledge_base --no-interactive

# 禁用特定输出
python -m src.main_cli --source ./docs --output ./knowledge_base --no-summaries --no-articles

# 使用自定义配置
python -m src.main_cli --source ./docs --output ./knowledge_base --config config.json
```

### Python API 使用（Phase 1 增强版）

```python
from src.main import KnowledgeCompiler
from src.core.config import Config, get_config

# 使用默认配置创建编译器
compiler = KnowledgeCompiler()

# 编译源目录中的所有文档
results = compiler.compile()

print(f"处理了 {results['processed_files']} 个文件")
print(f"提取了 {results['extracted_concepts']} 个概念")

# Phase 1：使用新的配置系统
config = get_config()
config.llm.provider = "openai"
config.llm.model = "gpt-4"
config.embeddings.enabled = True

compiler = KnowledgeCompiler(config)
results = compiler.compile()
```

### 配置（Phase 1 增强版）

```python
from src.core.config import Config, get_config

# 方法1：使用新的配置系统
config = get_config()
config.source_dir = "./docs"
config.output_dir = "./output"

# 配置 LLM 提供商
config.llm.provider = "openai"
config.llm.model = "gpt-4"
config.llm.api_key = "your-api-key"
config.llm.temperature = 0.7

# 启用嵌入
config.embeddings.enabled = True
config.embeddings.model = "text-embedding-ada-002"

# 配置状态管理
config.state.enabled = True
config.state.file = "./state.json"

# 初始化编译器
compiler = KnowledgeCompiler(config)

# 方法2：从文件加载
config = Config.from_file("config.json")
compiler = KnowledgeCompiler(config)
```

### 交互模式

```python
# 运行交互式编译会话
results = compiler.run_interactive_session()

# 手动审查概念
confirmed_concepts = compiler.review_concepts(extracted_concepts)

# Phase 1：使用 LLM 辅助增强
config.interactive_mode = True
config.llm.provider = "anthropic"  # 使用 Claude 进行交互式辅助
compiler = KnowledgeCompiler(config)
results = compiler.run_interactive_session()
```

### Phase 2：知识发现

```python
from src.discovery import (
    KnowledgeDiscoveryEngine,
    InteractiveDiscovery,
    DiscoveryConfig
)
from src.core.concept_model import EnhancedConcept, ConceptType
from src.core.document_model import EnhancedDocument
from src.core.relation_model import Relation

# 创建发现配置
config = DiscoveryConfig(
    enable_explicit_mining=True,
    enable_implicit_mining=True,
    enable_statistical_mining=True,
    enable_semantic_mining=True,
    enable_temporal_detection=True,
    enable_causal_detection=True,
    enable_evolutionary_detection=True,
    enable_conflict_detection=True
)

# 初始化发现引擎
engine = KnowledgeDiscoveryEngine(config)

# 在知识库上运行发现
result = engine.discover(
    documents=your_documents,
    concepts=your_concepts,
    relations=existing_relations  # 可选
)

# 访问发现结果
print(f"发现了 {len(result.relations)} 个关系")
print(f"检测到 {len(result.patterns)} 个模式")
print(f"找到 {len(result.gaps)} 个差距")
print(f"生成了 {len(result.insights)} 个洞察")

# 交互式探索
interactive = InteractiveDiscovery(engine)
interactive.discover_and_store(documents, concepts, relations)

# 探索概念的关系
momentum_relations = interactive.explore_relations("Momentum")

# 按关键词查找模式
trading_patterns = interactive.find_patterns("trading")

# 分析域中的差距
technical_gaps = interactive.analyze_gaps_in_domain("technical_analysis")

# 获取顶级洞察
top_insights = interactive.get_top_insights(10)

# 用自然语言提问
answer = interactive.ask_question(
    "动量指标如何在趋势跟踪策略中使用？"
)
```

完整的工作示例，请参见 `examples/discovery_example.py`。

## 配置选项

### Phase 1 配置系统

新的配置系统提供分层、经过验证的设置：

```python
@dataclass
class Config:
    # 核心设置
    source_dir: str
    output_dir: str
    file_patterns: List[str]

    # LLM 配置
    llm: LLMConfig

    # 嵌入配置
    embeddings: EmbeddingsConfig

    # 状态管理
    state: StateConfig

    # 处理设置
    processing: ProcessingConfig

    # 输出设置
    output: OutputConfig
```

### 传统配置（仍支持）

旧的 `Config` 类仍然可用以保持向后兼容：

```python
from src.config import Config  # 传统配置

config = Config(
    source_dir="./docs",
    output_dir="./output",
    template_dir="templates",
    max_file_size=10 * 1024 * 1024,
    recursive_processing=True,
    file_patterns=["*.md"],
    api_key="your-key",
    model_name="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=2000,
    min_confidence_threshold=0.6,
    max_concepts_per_document=20,
    enable_relation_extraction=True,
    generate_backlinks=True,
    generate_summaries=True,
    generate_articles=True,
    output_format="markdown",
    interactive_mode=True,
    verbose_output=False,
    quiet_mode=False
)
```

### 从文件加载配置

```python
# 从 JSON 文件加载
config = Config.from_file("config.json")

# 从字典加载
config_data = {
    "source_dir": "./docs",
    "output_dir": "./output",
    "interactive_mode": True
}
config = Config.from_dict(config_data)
```

## 架构

### Phase 1 架构

Knowledge Compiler 2.0 具有模块化、分层架构：

#### 核心层（Phase 1 新增）
- **基础模型**：所有域模型的抽象基类
- **文档模型**：具有验证功能的增强文档表示
- **概念模型**：具有灵活属性的丰富概念模型
- **关系模型**：概念之间复杂的关系映射
- **状态管理器**：用于增量编译的持久化状态跟踪
- **配置**：具有验证功能的分层配置

#### 集成层（Phase 1 新增）
- **LLM 提供商**：OpenAI、Anthropic 和 Ollama 的统一接口
- **嵌入**：概念和文档的语义嵌入生成
- **重试逻辑**：指数退避的自动重试
- **错误处理**：全面的错误处理和恢复

#### 处理层
- **分析器**：
  - **DocumentAnalyzer**：解析和结构化 Markdown 文档
  - **HashCalculator**：为文档创建唯一标识符

- **提取器**：
  - **ConceptExtractor**：识别和提取关键概念
  - 使用模式匹配和 AI 分析
  - 支持多种概念类型（术语、指标、策略等）

- **生成器**：
  - **ArticleGenerator**：从概念创建详细文章
  - **SummaryGenerator**：生成文档摘要
  - **BacklinkGenerator**：创建概念之间的交叉引用

- **索引器**：
  - **FileIndexer**：管理文档查找和组织
  - **CategoryIndexer**：按类别和标签组织文档
  - **RelationMapper**：映射概念之间的关系

#### 工具
- **FileOps**：基本的文件操作和 Markdown 发现
- **MarkdownUtils**：Markdown 解析和处理工具

### Phase 2：代码审查架构改进（2025年4月）

代码审查引入了几项架构增强：

#### 安全增强
- **路径验证**：所有文件操作现在都验证路径以防止遍历攻击
- **API 密钥编辑**：敏感凭据自动从错误消息中编辑
- **输入清理**：对所有用户输入进行全面验证

#### 性能优化
- **内容缓存**：文档读取一次并缓存，消除冗余 I/O
- **算法优化**：字符串操作从 O(n²) 改进到 O(n) 复杂度
- **缓存效率**：使用 `collections.OrderedDict` 实现正确的 LRU 缓存

#### 代码质量改进
- **依赖注入**：`KnowledgeCompiler` 支持组件注入以获得更好的可测试性
- **模块化设计**：组件可以交换或模拟以进行测试
- **可维护性**：清晰的关注点分离和减少耦合

```python
# 示例：依赖注入的实际应用
from src.main import KnowledgeCompiler
from src.analyzers.document_analyzer import DocumentAnalyzer

# 为测试注入自定义分析器
mock_analyzer = DocumentAnalyzer()
compiler = KnowledgeCompiler(document_analyzer=mock_analyzer)
```

## 数据模型

### Phase 1 增强模型

#### 文档（增强版）
```python
from src.core.document_model import Document

@dataclass
class Document:
    """具有验证和嵌入功能的增强文档模型"""
    path: str
    title: str
    content: str
    metadata: Dict[str, Any]
    sections: List[Section]
    hash: str
    embedding: Optional[np.ndarray] = None  # Phase 1: 语义嵌入
    created_at: datetime = field(default_factory=datetime.now)

    def validate(self) -> bool:
        """验证文档结构和内容"""
        pass
```

#### 概念（增强版）
```python
from src.core.concept_model import Concept

@dataclass
class Concept:
    """具有灵活属性的增强概念模型"""
    name: str
    type: ConceptType
    definition: str
    criteria: Optional[str] = None
    applications: List[Dict[str, str]] = field(default_factory=list)
    cases: List[str] = field(default_factory=list)
    formulas: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    backlinks: List[Dict[str, str]] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None  # Phase 1: 语义嵌入
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        pass

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Concept':
        """从字典反序列化"""
        pass
```

#### 关系（Phase 1 新增）
```python
from src.core.relation_model import Relation, RelationType

@dataclass
class Relation:
    """表示概念之间的关系"""
    source: str
    target: str
    relation_type: RelationType
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class RelationType(Enum):
    """关系类型"""
    DEFINES = "定义"
    RELATES_TO = "相关"
    DEPENDS_ON = "依赖"
    CONTRADICTS = "矛盾"
    EXTENDS = "扩展"
    USES = "使用"
    EXAMPLE_OF = "示例"
```

### 传统模型（仍支持）

#### 文档（传统版）
```python
from src.models.document import Document

@dataclass
class Document:
    path: str
    hash: str
    metadata: Dict[str, Any]
    sections: List[Section]
    content: str
```

#### 概念（传统版）
```python
from src.models.concept import Concept

@dataclass
class Concept:
    name: str
    type: ConceptType
    definition: str
    criteria: str
    applications: List[Dict[str, str]]
    cases: List[str]
    formulas: List[str]
    related_concepts: List[str]
    backlinks: List[Dict[str, str]]
```

### 概念类型
- **TERM**：通用术语和术语表
- **INDICATOR**：技术指标和度量
- **STRATEGY**：交易策略和方法
- **THEORY**：理论框架和模型
- **PERSON**：人物及其贡献

## 交互功能

### 概念确认
```python
# 交互式确认提取的概念
confirmed = compiler.confirm_concepts(extracted_concepts)

# 单独审查概念
reviewed = compiler.review_concepts(extracted_concepts)
```

### 交互会话
```python
# 运行完整的交互式编译会话
results = compiler.run_interactive_session()

# 访问编译结果
print(f"确认的概念：{results.get('confirmed_concepts', 0)}")
print(f"生成的文章：{results.get('generated_articles', 0)}")
```

## 错误处理和日志记录

系统提供全面的错误处理和日志记录：

```python
# 配置日志级别
config = Config(verbose_output=True)  # DEBUG 级别
config = Config(quiet_mode=True)      # 仅 ERROR 级别

# 访问编译统计
stats = compiler.get_processing_statistics()
```

## 示例

### Phase 2：知识发现

```python
# 运行发现示例
python examples/discovery_example.py

# 或在代码中导入和使用
from src.discovery import KnowledgeDiscoveryEngine, DiscoveryConfig

config = DiscoveryConfig()
engine = KnowledgeDiscoveryEngine(config)
result = engine.discover(documents, concepts, relations)
```

### 基本编译
```python
from src.main import KnowledgeCompiler

# 初始化编译器
compiler = KnowledgeCompiler()

# 编译所有文档
results = compiler.compile()

# 生成报告
compiler.save_results_report("compilation_report.md")
```

### 自定义配置
```python
from src.config import Config
from src.main import KnowledgeCompiler

# 自定义配置
config = Config(
    source_dir="./knowledge_base",
    output_dir="./wiki_output",
    file_patterns=["*.md", "*.markdown"],
    interactive_mode=False,
    generate_articles=True,
    generate_summaries=True,
    generate_backlinks=True
)

compiler = KnowledgeCompiler(config)
results = compiler.compile()
```

### 交互式工作流
```python
from src.main import KnowledgeCompiler

# 使用交互模式初始化
config = Config(interactive_mode=True)
compiler = KnowledgeCompiler(config)

# 运行交互式编译
results = compiler.run_interactive_session()

# 审查和更新概念
concepts = compiler.extracted_concepts
for concept in concepts:
    print(f"概念：{concept.name}")
    print(f"定义：{concept.definition}")
    # 交互式更新将在此处进行
```

## 测试

### 测试覆盖率

项目保持全面的测试覆盖率：

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_integration.py

# 运行覆盖率测试
pytest --cov=src --cov-report=term-missing

# 运行 Phase 2 代码审查验证测试
python test_phase2_review_fixes.py
```

### Phase 2 测试统计

- **总覆盖率**：85%+（全面的发现模块覆盖）
- **测试数量**：117 个发现功能测试（全部通过）
- **发现组件**：90-100% 覆盖率
- **集成测试**：端到端发现管道已验证

### 代码审查验证测试（2025年4月）

- **安全测试**：路径遍历攻击防护（2/2 测试通过）
- **性能测试**：冗余 I/O 消除，O(n²) → O(n) 优化验证
- **质量测试**：API 密钥保护、依赖注入、LRU 缓存实现
- **总体结果**：6/6 验证测试通过（100%）
- **回归测试**：所有现有功能均保留

## 开发状态

### 当前状态：Phase 2 完成并安全加固 ✅

**Phase 1：基础和核心增强**（已完成）
- ✅ 具有验证功能的增强数据模型
- ✅ LLM 提供商集成（OpenAI、Anthropic、Ollama）
- ✅ 用于语义搜索的嵌入生成
- ✅ 用于增量编译的状态管理
- ✅ 全面的测试覆盖率（82%）
- ✅ 文档更新

**Phase 2：知识发现引擎**（已完成）
- ✅ 智能关系挖掘（显式、隐式、统计、语义）
- ✅ 模式检测（时间、因果、进化、冲突）
- ✅ 差距分析（概念、关系、证据）
- ✅ 具有显著性评分的洞察生成
- ✅ 交互式探索 API
- ✅ 117 个全面测试（全部通过）
- ✅ 完整的文档和示例

**Phase 2：代码审查与安全改进**（已完成 - 2025年4月）
- ✅ 安全：消除路径遍历漏洞（HIGH 优先级）
- ✅ 安全：防止错误消息中的 API 密钥泄露（MEDIUM 优先级）
- ✅ 性能：文件 I/O 操作减少 50%（HIGH 优先级）
- ✅ 性能：O(n²) → O(n) 算法优化（MEDIUM 优先级）
- ✅ 架构：依赖注入以获得更好的可测试性（MEDIUM 优先级）
- ✅ 性能：正确的 LRU 缓存实现（MEDIUM 优先级）
- ✅ 6 个验证测试创建并通过（100%）
- ✅ 在 `docs/Phase2_Code_Review_Fixes_Summary.md` 中的全面文档

### 即将推出的阶段

**Phase 3：生产加固**（计划中）
- 可扩展性改进
- 监控和指标
- 部署自动化
- 高级错误处理
- 额外的性能优化

## 迁移指南

### 从传统版本到 Phase 1

#### 配置迁移

**旧方法：**
```python
from src.config import Config

config = Config(
    api_key="key",
    model_name="gpt-3.5-turbo",
    temperature=0.7
)
```

**新方法：**
```python
from src.core.config import get_config

config = get_config()
config.llm.api_key = "key"
config.llm.model = "gpt-4"
config.llm.temperature = 0.7
```

#### 数据模型迁移

**旧方法：**
```python
from src.models.document import Document
from src.models.concept import Concept
```

**新方法：**
```python
from src.core.document_model import Document
from src.core.concept_model import Concept

# 增强模型包括：
# - 验证方法
# - 嵌入支持
# - 更好的序列化
```

#### 添加 LLM 集成

```python
# 之前：无 LLM 支持
compiler = KnowledgeCompiler()

# 之后：使用 LLM
config = get_config()
config.llm.provider = "openai"
config.llm.model = "gpt-4"
compiler = KnowledgeCompiler(config)
```

#### 添加嵌入

```python
# 启用嵌入
config.embeddings.enabled = True
config.embeddings.model = "text-embedding-ada-002"

# 概念现在将具有语义嵌入
concepts = compiler.extracted_concepts
for concept in concepts:
    if concept.embedding is not None:
        print(f"{concept.name} 具有嵌入向量")
```

### 从 Phase 1 到 Phase 2

#### 添加知识发现

```python
# Phase 1：基本编译
from src.main import KnowledgeCompiler
from src.core.config import get_config

config = get_config()
compiler = KnowledgeCompiler(config)
results = compiler.compile()
documents = compiler.processed_documents
concepts = compiler.extracted_concepts

# Phase 2：添加知识发现
from src.discovery import KnowledgeDiscoveryEngine, DiscoveryConfig

discovery_config = DiscoveryConfig(
    enable_explicit_mining=True,
    enable_implicit_mining=True,
    enable_statistical_mining=True,
    enable_semantic_mining=True
)

discovery_engine = KnowledgeDiscoveryEngine(
    config=discovery_config,
    llm_provider=compiler.llm_provider,  # 重用编译器的 LLM
    embedding_generator=compiler.embedding_generator  # 重用嵌入器
)

# 在编译的知识上运行发现
discovery_result = discovery_engine.discover(
    documents=documents,
    concepts=concepts,
    relations=compiler.extracted_relations  # 现有关系
)

# 访问发现结果
print(f"发现了 {len(discovery_result.relations)} 个新关系")
print(f"检测到 {len(discovery_result.patterns)} 个模式")
print(f"找到 {len(discovery_result.gaps)} 个知识差距")
print(f"生成了 {len(discovery_result.insights)} 个洞察")
```

#### 交互式知识探索

```python
# Phase 2：添加交互式探索
from src.discovery import InteractiveDiscovery

interactive = InteractiveDiscovery(discovery_engine)
interactive.discover_and_store(documents, concepts, relations)

# 交互式探索知识库
momentum_relations = interactive.explore_relations("Momentum")
trading_patterns = interactive.find_patterns("trading strategy")
technical_gaps = interactive.analyze_gaps_in_domain("technical analysis")

# 获取顶级洞察
top_insights = interactive.get_top_insights(10)

# 用自然语言提问
answer = interactive.ask_question(
    "动量交易策略中最常见的模式是什么？"
)
```

#### 与现有工作流集成

```python
# 完整的 Phase 1 + Phase 2 工作流
from src.main import KnowledgeCompiler
from src.discovery import KnowledgeDiscoveryEngine, InteractiveDiscovery
from src.core.config import get_config

# 步骤1：编译文档（Phase 1）
config = get_config()
config.source_dir = "./docs"
config.output_dir = "./output"

compiler = KnowledgeCompiler(config)
compilation_result = compiler.compile()

# 步骤2：发现知识（Phase 2）
discovery_config = DiscoveryConfig()
discovery_engine = KnowledgeDiscoveryEngine(discovery_config)
discovery_result = discovery_engine.discover(
    documents=compiler.processed_documents,
    concepts=compiler.extracted_concepts
)

# 步骤3：交互式探索（Phase 2）
interactive = InteractiveDiscovery(discovery_engine)
interactive.discover_and_store(
    documents=compiler.processed_documents,
    concepts=compiler.extracted_concepts
)

# 现在你有了一个完整的、可探索的知识库！
```

## 性能

### Phase 1 基准测试

- **文档处理**：每个文档约 100ms
- **概念提取**：每个文档约 200ms
- **嵌入生成**：每 100 个概念约 500ms（批处理）
- **状态持久化**：每次保存约 50ms
- **测试套件**：429 个测试约 20 秒

### Phase 2 基准测试

- **关系挖掘**：每 100 个概念约 500ms
- **模式检测**：每 100 个概念约 300ms
- **差距分析**：每 100 个概念约 200ms
- **洞察生成**：每 100 个洞察约 1s（使用 LLM）
- **完整发现管道**：100 个文档约 2-3s
- **发现测试套件**：117 个测试约 15 秒

### 代码审查性能改进（2025年4月）

- **文件 I/O**：冗余磁盘操作减少 50%（使用缓存内容）
- **字符串操作**：关系查找中的 O(n²) → O(n) 复杂度
- **缓存效率**：正确的 LRU 实现提高命中率
- **整体影响**：更快的概念提取和更好的可扩展性

### 可扩展性

- 测试多达 1000 个文档
- 处理多达 10MB 的文档
- 使用流的高效内存使用
- 增量编译减少重新处理
- 发现引擎随概念数量线性扩展
- 大型知识库的批处理
- **安全**：路径验证防止未授权的文件访问
- **架构**：依赖注入实现更好的测试和模块化

## 贡献

1. Fork 仓库
2. 创建功能分支
3. 为新功能添加测试
4. 确保所有测试通过
5. 提交拉取请求

## 许可证

本项目采用 MIT 许可证。
