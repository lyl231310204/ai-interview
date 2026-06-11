"""
开发辅助 API —— 生成测试数据。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.interview_dataset import InterviewDataset

router = APIRouter()

# 模拟技术问答数据
MOCK_QA = [
    {
        "job_title": "Java后端开发工程师",
        "topic": "Spring Boot自动配置",
        "question": "请解释Spring Boot的自动配置原理，结合你项目中的使用经验说明。",
        "answer": "Spring Boot通过@EnableAutoConfiguration和AutoConfigurationImportSelector类实现自动配置。它读取META-INF/spring.factories文件中所有的自动配置类，然后根据@Conditional注解和classpath中存在的jar来判断哪些配置应该生效。我在项目中自定义了starter来封装公司统一的日志和监控组件，基于此原理实现了开箱即用。",
        "scores": {"correctness": 8, "depth": 7, "logic": 8, "practice": 9},
    },
    {
        "job_title": "Java后端开发工程师",
        "topic": "MySQL索引优化",
        "question": "你在项目中是如何优化MySQL查询性能的？举个具体例子。",
        "answer": "我们订单表有上千万数据，查询经常超时。我做了几件事：1) 用EXPLAIN分析执行计划，发现全表扫描；2) 建了覆盖索引避免回表；3) 对时间字段做了分区表按月分区；4) 热点数据用Redis缓存。优化后查询从3秒降到80ms。",
        "scores": {"correctness": 9, "depth": 8, "logic": 8, "practice": 9},
    },
    {
        "job_title": "前端开发工程师",
        "topic": "Vue3响应式原理",
        "question": "Vue3的响应式系统和Vue2有什么本质区别？Proxy相比Object.defineProperty解决了什么问题？",
        "answer": "Vue3用Proxy替代了Vue2的Object.defineProperty。Proxy可以直接拦截整个对象的所有操作，而defineProperty只能劫持已有属性。这解决了Vue2的三个痛点：1) 无法检测属性的新增和删除；2) 对数组操作（push/pop/splice）需要额外处理；3) 需要深度遍历所有属性。我们项目迁移到Vue3后，大数据列表的性能提升了约40%。",
        "scores": {"correctness": 9, "depth": 8, "logic": 9, "practice": 8},
    },
    {
        "job_title": "DevOps运维开发工程师",
        "topic": "K8s集群管理",
        "question": "你管理过Kubernetes集群吗？遇到过什么挑战？如何解决的？",
        "answer": "我管理过生产环境的K8s集群，主要挑战是资源调度和故障恢复。我们遇到了节点内存不足导致的Pod被驱逐问题，解决方案是设置了合理的resource request/limit，配置了HPA自动扩缩容，并加了NodeAffinity确保核心服务分散部署。还搭建了Prometheus+AlertManager的监控告警体系，MTTR从30分钟降到5分钟。",
        "scores": {"correctness": 8, "depth": 7, "logic": 7, "practice": 9},
    },
    {
        "job_title": "算法工程师",
        "topic": "推荐系统冷启动",
        "question": "推荐系统冷启动问题你是怎么处理的？",
        "answer": "新用户冷启动我们用了几种策略：1) 基于人口统计学的协同过滤（年龄、地区等）；2) 新用户引导页收集初始偏好标签；3) 热门内容兜底。新物品冷启动用内容特征加规则召回，积累一定曝光后转模型排序。实际效果：新用户冷启动阶段的CTR提升了25%。",
        "scores": {"correctness": 8, "depth": 9, "logic": 8, "practice": 8},
    },
    {
        "job_title": "Java后端开发工程师",
        "topic": "分布式事务",
        "question": "你在项目中如何处理分布式事务？用过哪些方案？",
        "answer": "我们支付场景用了Seata AT模式保证强一致性，非核心场景用MQ最终一致性。AT模式通过全局事务协调器和undo日志实现自动回滚，对业务侵入小。MQ方案通过本地消息表加定时任务保证可靠投递。有一个关键教训：AT模式在长事务场景下锁持有时间太长，后来限制了事务超时并加了降级开关。",
        "scores": {"correctness": 8, "depth": 8, "logic": 7, "practice": 9},
    },
    {
        "job_title": "前端开发工程师",
        "topic": "Webpack构建优化",
        "question": "你们的Webpack构建太慢了，怎么优化？",
        "answer": "我们项目构建从3分钟优化到了40秒。具体做了：1) 升级到Webpack5启用持久化缓存；2) 配置thread-loader多线程编译；3) DLL预编译第三方库；4) 用esbuild替代terser做压缩；5) 开发环境用esbuild-loader。最大的收益来自持久化缓存，增量编译只需2-3秒。",
        "scores": {"correctness": 8, "depth": 7, "logic": 9, "practice": 9},
    },
    {
        "job_title": "DevOps运维开发工程师",
        "topic": "CI/CD流水线",
        "question": "描述一下你搭建的CI/CD流水线是什么样的？",
        "answer": "我们用GitLab CI + Jenkins编排了完整的CI/CD流程。代码push → 自动触发单元测试和代码扫描（SonarQube）→ 构建Docker镜像 → 推送Harbor仓库 → K8s滚动更新。生产发布有审批卡点，需要Team Leader确认。灰度发布用Istio做流量切分，先10%观察30分钟再全量。",
        "scores": {"correctness": 8, "depth": 8, "logic": 9, "practice": 8},
    },
]


@router.post("/dev/generate-test-data")
def generate_test_data(db: Session = Depends(get_db)):
    """生成模拟面试数据集用于测试。"""
    count = 0
    for qa in MOCK_QA:
        existing = db.query(InterviewDataset).filter(
            InterviewDataset.question == qa["question"]
        ).first()
        if existing:
            continue
        record = InterviewDataset(
            interview_id=count + 100,
            job_title=qa["job_title"],
            question=qa["question"],
            answer=qa["answer"],
            topic=qa["topic"],
            scores=qa["scores"],
            prompt_version_used="v1.0",
            answer_length=len(qa["answer"]),
        )
        db.add(record)
        count += 1
    db.commit()
    return {"code": 0, "message": f"已生成 {count} 条测试数据", "total": count}
