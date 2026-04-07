# KnowledgeMiner 4.0 设计方案

**设计日期**: 2026-04-07
**版本**: 4.0
**架构模式**: LLM Wiki + 三层架构
**实施策略**: 一次性彻底重构

---

## 执行摘要

KnowledgeMiner 4.0 是基于**LLM Wiki模式**的彻底重构版本，采用**三层架构**实现知识管理的完整闭环。

### 核心决策

- ✅ **Wiki作为主要输出格式**：用户主要看到wiki页面
- ✅ **三层架构**：Raw Sources → Enhanced Models → Wiki Models
- ✅ **完全遵循LLM Wiki约定**：index.md + log.md + 标准目录结构
- ✅ **按类别组织sources**：papers/articles/reports/notes
- ✅ **全新实现废弃旧代码**：在新分支从零开始

### 预期收益

- 🎯 **彻底解决模型兼容性问题**：单一模型体系
- 🎯 **功能完整**：保留所有discovery功能
- 🎯 **性能优化**：三层缓存，批处理
- 🎯 **用户体验**：Obsidian兼容，图形化知识图谱
- 🎯 **维护性**：清晰的职责分离，易于扩展

---

## 第一部分：核心架构

### 系统架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    KnowledgeMiner 4.0                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Raw Sources         Enhanced Models        Wiki Models      │
│  (不可变输入)    →    (处理层)       →    (持久化层)   │
│                                                               │
│  ┌──────────┐      ┌─────────────┐       ┌──────────┐      │
│  │ papers/  │      │EnhancedConcept│      │WikiPage  │      │
│  │articles/ │  →   │EnhancedDocument│  →   │WikiUpdate│      │
│  │reports/  │      │DiscoveryResult │     │...       │      │
│  │notes/    │      │PatternEvidence │      └──────────┘      │
│  └──────────┘      └─────────────┘             │             │
│                                               ↓             │
│                                          ┌──────────┐      │
│                                          │ Wiki文件  │      │
│                                          │ (Markdown)│     │
│                                          └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 三层职责

**第1层：Raw Sources（数据输入层）**
- **职责**：存储原始来源文档，不可变
- **格式**：markdown文件 + YAML frontmatter
- **结构**：
  ```
  raw/
  ├── papers/          # 学术论文
  ├── articles/        # 文章
  ├── reports/         # 研究报告
  └── notes/           # 笔记
  ```
- **特性**：LLM只读，不修改

**第2层：Enhanced Models（处理层）**
- **职责**：知识提取、分析、关联推理
- **模型**：EnhancedConcept, EnhancedDocument, DiscoveryResult
- **功能**：
  - 概念提取和关系挖掘
  - 模式检测和gap分析
  - 证据收集和置信度评分
  - 语义嵌入生成
- **输出**：结构化的发现结果

**第3层：Wiki Models（持久化层）**
- **职责**：Wiki页面的创建、更新、维护
- **模型**：WikiPage, WikiUpdate, WikiIndex
- **格式**：Markdown文件，Obsidian兼容
- **结构**：
  ```
  wiki/
  ├── index.md         # 目录索引（所有页面列表）
  ├── log.md           # 更新日志（append-only）
  ├── entities/        # 实体页面（人名、机构等）
  ├── concepts/        # 概念页面（抽象概念）
  ├── sources/         # 来源摘要
  ├── synthesis/       # 综合分析
  └── comparisons/     # 对比分析
  ```

### 核心操作流程

**1. INGEST（知识摄入）**
```
Raw Source → Enhanced处理 → Wiki更新
     ↓            ↓             ↓
  新文档    概念提取+分析   创建/更新页面
                      (10-15个wiki页面)
```

**2. QUERY（知识查询）**
```
用户问题 → 搜索index.md → 读取相关页面 → 生成答案
                                    ↓
                            可选：存入wiki作为新页面
```

**3. LINT（健康检查）**
```
遍历wiki → 检测问题 → 修复建议
  ↓           ↓          ↓
所有页面    矛盾/孤立/   自动修复
          过时信息
```

---

## 第二部分：数据模型设计

### 第1层：Raw Sources模型

**格式约定**：标准Markdown + Frontmatter

```markdown
---
title: "Deep Learning in Finance"
source_type: "paper"
authors: ["Author A", "Author B"]
date: 2026-04-01
url: "https://..."
tags: ["finance", "deep-learning", "prediction"]
---

# Content here...
```

**类别规范**：
- `papers/`: 学术论文，有正式引用格式
- `articles/`: 新闻/博客文章
- `reports/`: 研究报告，数据驱动
- `notes/`: 用户笔记，非正式

---

### 第2层：Enhanced Models（处理层）

#### 核心模型

**EnhancedConcept**（概念模型）
```python
class EnhancedConcept(BaseModel):
    """增强概念模型 - 用于知识提取和分析"""

    # 基础属性
    name: str
    type: ConceptType  # ENUM: ENTITY, ABSTRACT, RELATION, METHOD
    definition: str

    # 增强功能
    embeddings: Optional[np.ndarray] = None  # 语义嵌入
    confidence: float = 0.5                   # 置信度 0-1

    # 知识关联
    properties: Dict[str, Any] = {}           # 动态属性
    relations: List[str] = []                 # 关联概念
    evidence: List[Dict[str, Any]] = []       # 证据支持

    # 元数据
    temporal_info: Optional[TemporalInfo] = None
    source_documents: List[str] = []          # 来源文档ID

    # 业务方法
    def add_evidence(self, source: str, quote: str, confidence: float)
    def add_relation(self, concept_name: str)
    def update_confidence(self, confidence: float)
```

**EnhancedDocument**（文档模型）
```python
class EnhancedDocument(BaseModel):
    """增强文档模型 - 用于文档分析"""

    source_type: SourceType  # ENUM: FILE, URL, TEXT
    content: str

    # 元数据
    metadata: DocumentMetadata  # title, tags, file_path, authors...

    # 增强功能
    embeddings: Optional[np.ndarray] = None
    concepts: List[EnhancedConcept] = []
    relations: List[Relation] = []
    quality_score: float = 0.5

    # 业务方法
    def add_concept(self, concept: EnhancedConcept)
    def find_concepts_by_type(self, concept_type: ConceptType)
```

**DiscoveryResult**（发现结果）
```python
class DiscoveryResult(BaseModel):
    """知识发现结果"""

    # 发现类型
    result_type: DiscoveryType  # PATTERN, GAP, INSIGHT, CONTRADICTION

    # 内容
    summary: str
    significance_score: float
    confidence: float

    # 证据
    affected_concepts: List[str] = []
    evidence: List[Dict[str, Any]] = []

    # 元数据
    discovered_at: datetime = Field(default_factory=datetime.now)
    source_documents: List[str] = []
```

---

### 第3层：Wiki Models（持久化层）

**WikiPage**（Wiki页面）
```python
class WikiPage(BaseModel):
    """Wiki页面模型 - LLM Wiki格式"""

    # 页面标识
    id: str                    # 唯一ID
    title: str                 # 页面标题
    page_type: PageType        # ENTITY, CONCEPT, SOURCE, SYNTHESIS, COMPARISON

    # 内容
    content: str               # Markdown内容
    frontmatter: Dict[str, Any] = {}  # YAML frontmatter

    # 版本控制
    version: int = 1
    created_at: datetime
    updated_at: datetime

    # 关联
    links: List[str] = []      # 出链（链接到其他页面）
    backlinks: List[str] = []  # 入链（其他页面链接到此）

    # 元数据
    tags: List[str] = []
    sources_count: int = 0     # 多少个source支持此页面

    def to_markdown(self) -> str:
        """转换为markdown格式"""
```

**WikiUpdate**（Wiki更新记录）
```python
class WikiUpdate(BaseModel):
    """Wiki更新记录 - 用于log.md"""

    timestamp: datetime
    update_type: UpdateType    # INGEST, QUERY, LINT
    page_id: str
    changes: str               # 描述性变更
    parent_version: int        # 前一个版本
```

**WikiIndex**（Wiki索引）
```python
class WikiIndex(BaseModel):
    """Wiki索引 - index.md的结构"""

    categories: Dict[str, List[IndexEntry]] = {}
    last_updated: datetime

    def add_entry(self, category: str, entry: IndexEntry)
    def to_markdown(self) -> str  # 生成index.md内容
```

---

### 模型转换关系

```
Raw Source
    ↓ (parse)
EnhancedDocument
    ↓ (extract concepts)
List[EnhancedConcept]
    ↓ (discover patterns)
List[DiscoveryResult]
    ↓ (convert to wiki)
WikiPage
    ↓ (write file)
Markdown File in wiki/
```

---

## 第三部分：组件设计与核心流程

### 核心组件架构

```
src/
├── raw/                    # Raw Sources层
│   ├── source_loader.py    # 加载raw sources
│   ├── source_parser.py    # 解析markdown + frontmatter
│   └── categories.py       # 类别管理
│
├── enhanced/               # Enhanced Models层（处理层）
│   ├── models/             # EnhancedConcept, EnhancedDocument, DiscoveryResult
│   ├── extractors/         # 概念提取
│   │   ├── concept_extractor.py
│   │   └── relation_extractor.py
│   ├── discovery/          # 知识发现
│   │   ├── pattern_detector.py
│   │   ├── gap_analyzer.py
│   │   └── insight_generator.py
│   └── embeddings/         # 嵌入生成
│       └── embedding_generator.py
│
├── wiki/                   # Wiki Models层（持久化层）
│   ├── models/             # WikiPage, WikiUpdate, WikiIndex
│   ├── operations/         # 核心操作
│   │   ├── ingest.py       # INGEST操作
│   │   ├── query.py        # QUERY操作
│   │   └── lint.py         # LINT操作
│   ├── writers/            # Wiki写入
│   │   ├── page_writer.py  # 写入wiki页面
│   │   ├── index_writer.py # 更新index.md
│   │   └── log_writer.py   # 更新log.md
│   └── utils/
│       ├── linker.py       # 管理wiki链接
│       └── merger.py       # 合并页面更新
│
└── orchestrator.py         # 主控制器（编排所有操作）
```

---

### 核心流程设计

#### 1. INGEST流程（知识摄入）

```python
def ingest_source(source_path: str) -> IngestResult:
    """
    Ingest新source到wiki

    流程：
    1. 加载raw source
    2. 解析为EnhancedDocument
    3. 提取概念
    4. 发现模式/洞见
    5. 转换为wiki页面
    6. 更新index和log
    """

    # Step 1: 加载raw source
    source = SourceLoader.load(source_path)

    # Step 2: 解析为EnhancedDocument
    enhanced_doc = SourceParser.parse(source)

    # Step 3: 提取概念
    concepts = ConceptExtractor.extract(enhanced_doc)

    # Step 4: 知识发现
    discoveries = []
    discoveries.extend(PatternDetector.detect(concepts))
    discoveries.extend(GapAnalyzer.analyze(concepts))
    discoveries.extend(InsightGenerator.generate(concepts))

    # Step 5: 转换为wiki页面（10-15个页面）
    wiki_pages = []

    # 创建source摘要页
    wiki_pages.append(create_source_page(enhanced_doc))

    # 创建/更新概念页
    for concept in concepts:
        wiki_pages.append(update_concept_page(concept))

    # 创建/更新实体页
    for entity in extract_entities(concepts):
        wiki_pages.append(update_entity_page(entity))

    # 创建综合分析页
    wiki_pages.append(create_synthesis_page(discoveries))

    # Step 6: 写入wiki
    for page in wiki_pages:
        PageWriter.write(page)

    # Step 7: 更新index和log
    IndexWriter.update(wiki_pages)
    LogWriter.append_ingest(source_path, wiki_pages)

    return IngestResult(
        source=source_path,
        pages_created=len(wiki_pages),
        concepts_extracted=len(concepts),
        discoveries=len(discoveries)
    )
```

**影响的Wiki页面类型**：
- `wiki/sources/{source_id}.md` - 新建source摘要
- `wiki/concepts/{concept_name}.md` - 更新概念页
- `wiki/entities/{entity_name}.md` - 更新实体页
- `wiki/synthesis/{topic}.md` - 更新综合分析
- `wiki/index.md` - 更新索引
- `wiki/log.md` - 添加ingest记录

---

#### 2. QUERY流程（知识查询）

```python
def query(question: str) -> QueryResult:
    """
    查询wiki并生成答案

    流程：
    1. 解析问题
    2. 搜索index.md找到相关页面
    3. 读取相关页面
    4. 生成答案
    5. （可选）将答案存入wiki
    """

    # Step 1: 解析问题
    parsed = QueryParser.parse(question)

    # Step 2: 搜索index.md
    relevant_pages = IndexSearcher.search(parsed.keywords)

    # Step 3: 读取相关页面
    page_contents = []
    for page_id in relevant_pages:
        content = PageReader.read(page_id)
        page_contents.append(content)

    # Step 4: 生成答案
    answer = AnswerGenerator.generate(
        question=question,
        context=page_contents
    )

    # Step 5: 可选 - 将有价值的答案存入wiki
    if answer.is_worth_saving():
        # 创建新的wiki页面（如对比分析）
        new_page = create_page_from_answer(answer)
        PageWriter.write(new_page)
        IndexWriter.update([new_page])
        LogWriter.append_query(question, new_page.id)

    return QueryResult(
        question=question,
        answer=answer.content,
        sources=answer.citations,
        pages_created=1 if answer.is_worth_saving() else 0
    )
```

---

#### 3. LINT流程（健康检查）

```python
def lint_wiki() -> LintResult:
    """
    检查wiki健康状态并修复问题

    流程：
    1. 遍历所有wiki页面
    2. 检测问题
    3. 尝试自动修复
    4. 生成报告
    """

    issues = []
    fixes = []

    # Step 1: 遍历所有页面
    all_pages = PageReader.list_all()

    # Step 2: 检测问题

    # 检查矛盾
    contradictions = ContradictionDetector.detect(all_pages)
    issues.extend([f"矛盾: {c}" for c in contradictions])

    # 检查孤立页面
    orphans = OrphanDetector.find(all_pages)
    issues.extend([f"孤立页面: {o}" for o in orphans])

    # 检查缺失的交叉引用
    missing_refs = MissingRefDetector.check(all_pages)
    issues.extend([f"缺失引用: {r}" for r in missing_refs])

    # 检查过时信息
    stale = StaleInfoDetector.check(all_pages)
    issues.extend([f"过时信息: {s}" for s in stale])

    # Step 3: 自动修复
    for issue in issues:
        if fixable(issue):
            fix = AutoFixer.fix(issue)
            fixes.append(fix)
            PageWriter.write(fix.updated_page)

    # Step 4: 生成报告
    report = LintReport(
        total_pages=len(all_pages),
        issues_found=len(issues),
        issues_fixed=len(fixes),
        recommendations=generate_recommendations(issues)
    )

    # 更新log
    LogWriter.append_lint(report)

    return report
```

**Lint检测的问题类型**：
- 矛盾：不同页面表达相互冲突的观点
- 孤立页面：没有被任何其他页面链接
- 缺失引用：提到的概念但没有创建对应页面
- 过时信息：新source使得旧内容过时
- 数据gap：可以通过web搜索填充的缺失信息

---

### 文件组织结构

```
KnowledgeMiner/
├── raw/                      # Raw Sources（不可变）
│   ├── papers/
│   │   └── deep-learning-finance.md
│   ├── articles/
│   │   └── market-analysis.md
│   ├── reports/
│   └── notes/
│
├── wiki/                     # Wiki（LLM维护）
│   ├── index.md              # 主索引
│   ├── log.md                # 更新日志
│   ├── entities/
│   │   ├── OpenAI.md
│   │   └── Anthropic.md
│   ├── concepts/
│   │   ├── Transformer.md
│   │   └── Fine-tuning.md
│   ├── sources/
│   │   └── deep-learning-finance.md
│   ├── synthesis/
│   │   └── llm-in-finance.md
│   └── comparisons/
│       └── gpt-vs-claude.md
│
├── src/                      # 源代码
│   ├── raw/
│   ├── enhanced/
│   ├── wiki/
│   └── orchestrator.py
│
├── tests/
├── docs/
└── config/                   # 配置文件
    └── schema.yaml           # Wiki schema约定
```

---

## 第四部分：实施计划与技术细节

### 1. 错误处理策略

#### 分层错误处理

**Raw Sources层**
```python
class SourceLoadError(Exception):
    """Source加载失败"""
    pass

class SourceParseError(Exception):
    """Source解析失败"""
    pass

# 处理策略：记录错误，跳过该source，继续处理
try:
    source = SourceLoader.load(path)
except SourceLoadError as e:
    logger.error(f"Failed to load {path}: {e}")
    continue
```

**Enhanced Models层**
```python
class ConceptExtractionError(Exception):
    """概念提取失败"""
    pass

class DiscoveryError(Exception):
    """知识发现失败"""
    pass

# 处理策略：降级处理，返回部分结果
try:
    concepts = ConceptExtractor.extract(doc)
except ConceptExtractionError as e:
    logger.warning(f"Partial extraction: {e}")
    concepts = []  # 返回空列表，继续处理
```

**Wiki Models层**
```python
class WikiWriteError(Exception):
    """Wiki写入失败"""
    pass

class WikiMergeConflict(Exception):
    """Wiki合并冲突"""
    pass

# 处理策略：版本控制，冲突解决
try:
    PageWriter.write(page)
except WikiMergeConflict as e:
    resolved = Merger.resolve_conflict(e.conflict)
    PageWriter.write(resolved)
```

---

### 2. 测试策略

#### 测试金字塔

```
        E2E Tests (10%)
       ┌──────────┐
      │           │
     │ Integration │ (30%)
    │   Tests     │
   │               │
  │ Unit Tests     │ (60%)
 └────────────────┘
```

**单元测试**（60%）
- 每个组件独立测试
- Mock外部依赖
- 覆盖率目标：>85%

**集成测试**（30%）
- 测试组件间交互
- 使用测试wiki和测试sources
- 验证数据流

**E2E测试**（10%）
- 完整流程测试
- 真实LLM调用
- 性能验证

---

### 3. 数据迁移策略

#### 从旧系统迁移到4.0

**阶段1：备份和隔离**（1天）
```bash
# 创建备份分支
git checkout -b backup/pre-4.0
git push origin backup/pre-4.0

# 创建新的4.0分支
git checkout -b feature/knowledgeminer-4.0
```

**阶段2：迁移现有sources**（1天）
```python
def migrate_legacy_sources():
    """将旧系统的sources迁移到新的raw/目录"""

    # 扫描旧output目录
    old_sources = scan_old_output_directory()

    for source in old_sources:
        # 按类别分类
        category = classify_source(source)

        # 添加frontmatter
        add_frontmatter(source, category)

        # 移动到新位置
        new_path = f"raw/{category}/{source.filename}"
        shutil.move(source.path, new_path)
```

**阶段3：重建wiki**（2-3天）
```python
def rebuild_wiki():
    """从sources重建整个wiki"""

    # 清空旧wiki
    shutil.rmtree("wiki/")
    os.makedirs("wiki/")

    # 重新ingest所有sources
    sources = glob("raw/**/*.md", recursive=True)
    for source in sources:
        ingest_source(source)

    # 运行lint修复问题
    lint_wiki()
```

**阶段4：验证和切换**（1天）
```python
def validate_migration():
    """验证迁移结果"""

    # 检查所有sources已ingest
    old_count = len(glob("output/**/*.md"))
    new_sources = len(glob("wiki/sources/*.md"))
    assert new_sources >= old_count, "Missing sources"

    # 检查概念完整性
    old_concepts = extract_legacy_concepts()
    new_concepts = extract_wiki_concepts()
    assert len(new_concepts) >= len(old_concepts) * 0.8, "Too many concepts lost"

    # 功能测试
    test_queries = [
        "What is the main topic?",
        "Compare different approaches",
        "What are the key findings?"
    ]
    for q in test_queries:
        result = query(q)
        assert result.answer, f"Query failed: {q}"
```

---

### 4. 性能优化策略

#### 缓存策略

**三层缓存**
```python
class CacheManager:
    """管理三层缓存"""

    def __init__(self):
        # L1: 内存缓存（概念数据）
        self.l1_cache = {}  # {concept_name: EnhancedConcept}

        # L2: 磁盘缓存（嵌入向量）
        self.l2_cache = DiskCache("cache/embeddings/")

        # L3: 数据库缓存（历史记录）
        self.l3_cache = sqlite3.connect("cache/history.db")

    def get_concept(self, name: str) -> Optional[EnhancedConcept]:
        # 先查L1
        if name in self.l1_cache:
            return self.l1_cache[name]

        # 再查L2
        cached = self.l2_cache.get(name)
        if cached:
            concept = EnhancedConcept.parse_raw(cached)
            self.l1_cache[name] = concept
            return concept

        # 最后查L3
        # ...
```

#### 批处理优化

```python
def batch_ingest(sources: List[str], batch_size: int = 10):
    """批量ingest，提高效率"""

    for i in range(0, len(sources), batch_size):
        batch = sources[i:i+batch_size]

        # 并行处理batch
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(ingest_source, s) for s in batch]
            results = [f.result() for f in futures]

        # 批量更新index（减少IO）
        IndexWriter.batch_update(results)
```

---

### 5. 实施时间表

| 阶段 | 任务 | 时间 | 依赖 |
|------|------|------|------|
| **Week 1** | | | |
| Day 1-2 | 创建项目结构和基础模型 | 2天 | - |
| Day 3-4 | 实现Source Loader/Parser | 2天 | 基础模型 |
| Day 5 | 实现Concept Extractor | 1天 | Source Parser |
| **Week 2** | | | |
| Day 6-7 | 实现Discovery组件 | 2天 | Concept Extractor |
| Day 8-9 | 实现Wiki Models和Writers | 2天 | Discovery |
| Day 10 | 实现Ingest流程 | 1天 | Writers |
| **Week 3** | | | |
| Day 11-12 | 实现Query流程 | 2天 | Wiki Models |
| Day 13 | 实现Lint流程 | 1天 | Wiki Models |
| Day 14-15 | 编写测试 | 2天 | 所有组件 |
| **Week 4** | | | |
| Day 16-17 | 数据迁移 | 2天 | 测试通过 |
| Day 18-19 | 集成测试和调试 | 2天 | 数据迁移 |
| Day 20 | 文档和部署 | 1天 | 集成测试 |

**总计：4周（20个工作日）**

---

### 6. 风险评估与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| LLM调用成本超预算 | 中 | 高 | 实现智能缓存，批处理优化 |
| Wiki页面质量不稳定 | 中 | 中 | 人工审核首批页面，建立质量标准 |
| 数据迁移丢失信息 | 低 | 高 | 完整备份，分阶段验证 |
| 性能不达标 | 低 | 中 | 性能基准测试，提前优化 |
| 用户体验下降 | 低 | 中 | 保留旧系统并行，逐步切换 |

---

## 第五部分：配置与扩展

### Schema配置（config/schema.yaml）

```yaml
# KnowledgeMiner 4.0 Wiki Schema

wiki:
  structure:
    index: "wiki/index.md"
    log: "wiki/log.md"
    directories:
      entities: "wiki/entities/"
      concepts: "wiki/concepts/"
      sources: "wiki/sources/"
      synthesis: "wiki/synthesis/"
      comparisons: "wiki/comparisons/"

  conventions:
    naming: "kebab-case"  # kebab-case for file names
    links: "wikilink"     # [[Page Name]] format
    frontmatter: true     # Always include YAML frontmatter

  quality:
    min_confidence: 0.6   # Minimum confidence to save concept
    max_concepts_per_source: 50
    min_sources_per_concept: 2

raw:
  categories:
    - papers
    - articles
    - reports
    - notes

  conventions:
    encoding: "utf-8"
    line_ending: "lf"
    require_frontmatter: true

enhanced:
  embeddings:
    model: "text-embedding-3-small"
    dimension: 1536
    cache_enabled: true

  discovery:
    patterns:
      enabled: true
      confidence_threshold: 0.7
    gaps:
      enabled: true
      severity_threshold: 0.5
    insights:
      enabled: true
      significance_threshold: 0.6

operations:
  ingest:
    batch_size: 10
    parallel_workers: 3

  query:
    max_results: 10
    context_window: 5

  lint:
    auto_fix: true
    check_interval: "daily"
```

---

## 总结：KnowledgeMiner 4.0 核心特性

✅ **三层清晰架构**：Raw → Enhanced → Wiki
✅ **LLM Wiki模式**：ingest/query/lint核心操作
✅ **完全统一模型**：废弃旧模型，单一体系
✅ **一次性重构**：全新实现，无历史包袱
✅ **Obsidian兼容**：标准markdown，支持graph view
✅ **高性能设计**：三层缓存，批处理优化
✅ **4周实施计划**：清晰的里程碑和验证点

---

**设计版本**: 1.0
**最后更新**: 2026-04-07
**设计者**: KnowledgeMiner 架构团队
