# KnowledgeMiner 3.0

一个综合性智能知识积累系统，将静态 Markdown 文档转换为动态、自维护的 Wiki，具备自动概念提取、关系发现、洞察生成和持续质量保证功能。

## 🎯 项目概述

KnowledgeMiner 3.0 是下一代知识管理系统，超越了一次性分析，创建了活的知识库。它自动处理文档、发现洞察、将发现回填到历史内容中，并通过智能监控和修复维护 Wiki 质量。

## ✨ 功能特性

### 🔄 Wiki 知识管理
- **持久化 Wiki 存储**：具有完整历史跟踪的版本控制知识库
- **自动维护**：当新文档到达时自动更新的 Wiki
- **批处理**：高效的每日/每周定期新文档处理
- **增量更新**：智能混合模式自动选择最佳更新策略
- **Wiki 组织**：基于主题的结构，具有自动分类和标记

### 🧠 智能知识发现
- **关系挖掘**：发现概念之间的显式、隐式、统计和语义关系
- **模式检测**：识别知识中的时间、因果、进化和冲突模式
- **差距分析**：自动查找缺失的概念、关系和证据
- **洞察生成**：生成具有多维优先级评分的可操作洞察
- **语义搜索**：跨所有 Wiki 内容的全文和语义搜索

### 💡 智能洞察管理
- **自动回填**：智能地将新洞察传播到相关历史页面
- **优先级评分**：多维评估（新颖性 × 影响力 × 可操作性）
- **智能传播**：直接传播到受影响的页面（最多 2 跳）并检测循环
- **队列管理**：基于优先级的回填，包含即时（P0）和批处理队列
- **影响分析**：当新洞察出现时评估哪些页面需要更新

### 🔍 质量保证系统
- **健康监控**：通过全面健康检查持续监控 Wiki 质量
- **一致性检查**：验证内部、交叉引用和时间一致性
- **问题分类**：智能问题分类（关键/重要/次要）
- **分级修复**：从手动 → 半自动 → 全自动修复的渐进自动化
- **质量指标**：跟踪健康评分、问题分布和质量趋势

### 🔒 安全与性能
- **路径遍历防护**：所有文件操作都经过验证以防止攻击
- **API 密钥安全**：自动在错误消息中编辑敏感凭据
- **内容缓存**：通过智能缓存减少 50% 的文件 I/O
- **算法优化**：O(n²) → O(n) 复杂度改进以提升可扩展性
- **依赖注入**：模块化架构以实现更好的可测试性和可维护性

### 🤖 LLM 集成
- **多提供商支持**：OpenAI、Anthropic Claude 和本地模型（Ollama）
- **语义嵌入**：自动生成概念和文档的嵌入
- **AI 辅助审查**：使用 LLM 辅助进行交互式概念确认
- **智能生成**：LLM 驱动的摘要、文章和反向链接生成

### 📊 文档分析
- **自动提取**：解析和结构化包含 frontmatter 的 Markdown 文档
- **概念识别**：提取关键概念、定义、标准和示例
- **关系映射**：映射概念之间的复杂关系
- **分类**：按类别和标签进行智能组织
- **置信度评分**：使用置信度指标评估提取质量

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

### 系统架构

KnowledgeMiner 3.0 采用模块化四组件架构，专为持久化知识积累设计：

#### 🗄️ WikiCore - 知识存储基础
- **WikiStore**：主题、概念和关系的统一存储
- **VersionLog**：具有 Git 集成的完整版本历史
- **KnowledgeGraph**：基于 NetworkX 的图操作
- **QueryEngine**：全文搜索（Whoosh）和语义查询
- **不可变存储**：仅追加写入以确保数据完整性

#### 🔍 DiscoveryPipeline 2.0 - 智能发现引擎
- **InputProcessor**：检测新文档、更改文档和已删除文档
- **ModeSelector**：在完全/增量/混合模式之间智能选择
- **DiscoveryOrchestrator**：集成关系挖掘、模式检测、差距分析
- **WikiIntegrator**：具有事务安全性的直接 Wiki 更新

#### 💡 InsightManager - 洞察生命周期管理
- **InsightReceiver**：收集、去重和索引洞察
- **PriorityScorer**：多维评分（新颖性、影响力、可操作性）
- **BackfillScheduler**：基于优先级的队列管理（P0-P3）
- **BackfillExecutor**：智能回填到受影响的页面
- **InsightPropagator**：具有循环检测的直接传播

#### 🛡️ QualitySystem - Wiki 健康守护者
- **HealthMonitor**：一致性、质量和陈旧性检测
- **IssueClassifier**：智能分类（关键/重要/次要）
- **分级修复系统**：渐进自动化（手动 → 半自动 → 自动）
- **QualityReporter**：指标、趋势和改进建议

### 文档处理层

#### 分析器
- **DocumentAnalyzer**：解析和结构化包含 frontmatter 的 Markdown 文档
- **HashCalculator**：为更改检测创建唯一标识符

#### 提取器
- **ConceptExtractor**：使用模式匹配识别和提取关键概念
- **RelationMiner**：发现显式、隐式、统计和语义关系
- **PatternDetector**：识别时间、因果、进化和冲突模式
- **GapAnalyzer**：查找缺失的概念、关系和证据
- **InsightGenerator**：生成具有显著性评分的可操作洞察

#### 生成器
- **ArticleGenerator**：从概念创建详细文章
- **SummaryGenerator**：生成文档摘要
- **BacklinkGenerator**：创建概念之间的交叉引用

### 集成层

#### LLM 提供商
- **OpenAI 集成**：用于文本生成和分析的 GPT 模型
- **Anthropic 集成**：用于高级推理的 Claude 模型
- **本地模型**：Ollama 支持以实现隐私和成本控制
- **统一接口**：所有提供商的一致 API

#### 嵌入和搜索
- **语义嵌入**：概念和文档的向量表示
- **全文搜索**：基于 Whoosh 的搜索，支持高亮显示
- **语义搜索**：使用嵌入进行向量相似度搜索
- **图导航**：使用 NetworkX 进行关系遍历

### 安全与质量

#### 安全功能
- **路径验证**：所有文件操作都经过验证以防止遍历攻击
- **API 密钥保护**：自动编辑敏感凭据
- **输入清理**：对所有用户输入进行全面验证
- **事务安全**：Wiki 更新的 ACID 保证

#### 性能优化
- **内容缓存**：文档读取一次并缓存（I/O 减少 50%）
- **算法优化**：O(n²) → O(n) 复杂度改进
- **LRU 缓存**：使用 OrderedDict 实现正确的缓存驱逐
- **批处理**：高效处理大型文档集

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

KnowledgeMiner 3.0 在所有组件中保持全面的测试覆盖率：

```bash
# 运行所有测试
pytest

# 运行特定测试套件
pytest tests/test_core/           # WikiCore 测试（80+ 个测试）
pytest tests/test_discovery/      # DiscoveryPipeline 测试（80+ 个测试）
pytest tests/test_insight/        # InsightManager 测试（90+ 个测试）
pytest tests/test_quality/        # QualitySystem 测试（55+ 个测试）
pytest tests/test_integration/    # 端到端测试（30+ 个测试）
pytest tests/test_resilience/     # 弹性测试（60+ 个测试）

# 运行覆盖率测试
pytest --cov=src --cov-report=term-missing

# 运行安全验证测试
python test_phase2_review_fixes.py
```

### 测试统计

- **总覆盖率**：所有模块 85%+
- **测试数量**：395+ 个测试（全部通过）
- **WikiCore**：80+ 个测试，完全覆盖
- **DiscoveryPipeline**：80+ 个测试，覆盖所有模式
- **InsightManager**：90+ 个测试，用于回填和传播
- **QualitySystem**：55+ 个测试，用于健康监控和修复
- **Resilience**：60+ 个测试，用于混沌工程和可扩展性
- **安全验证**：6/6 测试通过（100%）

### 测试类别

**单元测试**：单个组件测试
- 存储引擎操作
- 发现算法
- 洞察评分和传播
- 质量检查和修复

**集成测试**：端到端工作流
- 文档处理 → Wiki 更新
- 洞察发现 → 回填 → 传播
- 质量监控 → 问题检测 → 修复

**弹性测试**：生产就绪性
- 崩溃恢复和数据损坏
- 并发访问和竞态条件
- 大规模性能（10,000+ 页面）
- 迁移和回滚场景

**安全测试**：漏洞防护
- 路径遍历攻击防护
- 错误消息中的 API 密钥保护
- 输入验证和清理

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

我们欢迎对 KnowledgeMiner 3.0 的贡献！以下是入门方法：

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/gordon8018/KnowledgeMiner.git
cd KnowledgeMiner

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 以可编辑模式安装
pip install -e .
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行覆盖率测试
pytest --cov=src --cov-report=html

# 运行特定测试套件
pytest tests/test_wiki/test_core/
```

### 代码风格

- 遵循 PEP 8 风格指南
- 为所有函数使用类型提示
- 为所有模块、类和函数编写文档字符串
- 为新功能添加测试（目标是 >85% 的覆盖率）

### 提交更改

1. Fork 仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 为您的更改编写测试
4. 确保所有测试通过：`pytest`
5. 提交您的更改：`git commit -m "feat: add amazing feature"`
6. 推送到分支：`git push origin feature/amazing-feature`
7. 打开拉取请求

### 报告问题

报告错误或请求功能时：
- 使用清晰、描述性的标题
- 为错误提供最小的复现案例
- 包含环境详细信息（操作系统、Python 版本）
- 首先搜索现有问题

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件。

## 致谢

- **Phase 1 基础**：增强的数据模型、LLM 集成、嵌入
- **Phase 2 发现**：智能关系挖掘、模式检测、洞察生成
- **Phase 3 Wiki 系统**：持久化知识积累、质量保证、自动化
- **安全加固**：全面的代码审查和漏洞修复

用 ❤️ 构建，致力于智能知识管理。
