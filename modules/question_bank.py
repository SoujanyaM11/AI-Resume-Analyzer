"""Local interview question bank. Used in demo/fallback mode and to pad AI output.

Each entry: (skill, level, question, key_concepts). A concept may list synonyms separated by '|';
an answer "covers" the concept if it mentions any synonym. These concepts drive the non-AI
evaluator, so they are intentionally short and keyword-like.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

Q = Tuple[str, str, str, List[str]]

BANK: List[Q] = [
    # ---- Python
    ("Python", "Beginner", "What is the difference between a list and a tuple in Python, and when would you use each?",
     ["mutable|immutable", "tuple|fixed", "hashable|dictionary key", "performance|memory"]),
    ("Python", "Beginner", "Explain how Python dictionaries work and give a use case.",
     ["key", "value", "hash", "lookup|O(1)|constant"]),
    ("Python", "Intermediate", "What are decorators in Python and how would you write one?",
     ["function", "wrapper|wraps", "higher-order|takes a function|returns a function", "@"]),
    ("Python", "Intermediate", "Explain generators and why they can be more memory-efficient than lists.",
     ["yield", "lazy|on demand", "iterator", "memory"]),
    ("Python", "Advanced", "How does Python manage memory, and what is the GIL's effect on multi-threaded programs?",
     ["reference count|garbage collect", "GIL|global interpreter lock", "multiprocessing|processes", "I/O|cpu-bound"]),
    # ---- SQL
    ("SQL", "Beginner", "What is the difference between INNER JOIN and LEFT JOIN?",
     ["inner", "left", "null|unmatched", "matching rows|both tables"]),
    ("SQL", "Intermediate", "Explain GROUP BY versus WHERE versus HAVING.",
     ["group by|aggregate", "where|before", "having|after", "filter"]),
    ("SQL", "Advanced", "How do indexes speed up queries, and what are their trade-offs?",
     ["b-tree|tree", "index|lookup", "write|insert|update", "storage|space|explain|query plan"]),
    # ---- Pandas / NumPy / Data
    ("Pandas", "Beginner", "How would you handle missing values in a pandas DataFrame?",
     ["isna|isnull|null", "dropna|drop", "fillna|impute|mean|median", "domain|context|why"]),
    ("Pandas", "Intermediate", "What is the difference between merge, join and concat in pandas?",
     ["merge|key|column", "join|index", "concat|stack|axis", "inner|outer|left"]),
    ("NumPy", "Intermediate", "Why is NumPy faster than plain Python lists for numeric work?",
     ["vectorized|vectorised|vectorization", "contiguous|memory", "C|compiled", "broadcast"]),
    ("Statistics", "Beginner", "Explain mean, median and mode, and when the median is better than the mean.",
     ["mean", "median", "mode", "outlier|skew"]),
    ("Statistics", "Intermediate", "What is a p-value and how do you interpret it in a hypothesis test?",
     ["null hypothesis", "probability", "significance|alpha|0.05", "not proof|does not prove|effect size"]),
    ("Data Visualization", "Beginner", "How do you choose the right chart for a dataset?",
     ["audience", "comparison|trend|distribution|relationship", "bar|line|scatter|histogram", "clutter|simple|label"]),
    ("Excel", "Beginner", "How would you use VLOOKUP/XLOOKUP and pivot tables to analyse data?",
     ["lookup", "pivot", "summar|aggregate", "range|table"]),
    # ---- ML / DL / NLP
    ("Machine Learning", "Beginner", "What is overfitting and how can you prevent it?",
     ["training|train", "generaliz|generalis|unseen", "regulariz|regularis|dropout", "cross-validation|validation|more data"]),
    ("Machine Learning", "Intermediate", "Explain precision, recall and F1. When would you prefer recall?",
     ["precision", "recall", "f1|harmonic", "false negative|imbalanced|cost"]),
    ("Machine Learning", "Intermediate", "How would you evaluate a classification model on an imbalanced dataset?",
     ["accuracy|misleading", "precision|recall|f1|roc|pr curve", "stratif|resampl|smote|class weight", "confusion matrix"]),
    ("Machine Learning", "Advanced", "Explain the bias-variance trade-off and how you would diagnose it from learning curves.",
     ["bias", "variance", "underfit", "overfit|complexity"]),
    ("Deep Learning", "Intermediate", "What is backpropagation and why do we need activation functions?",
     ["gradient", "chain rule|derivative", "non-linear|nonlinear", "weights|update"]),
    ("Deep Learning", "Advanced", "How do vanishing gradients occur and what techniques mitigate them?",
     ["gradient", "relu|activation", "residual|skip|batch norm|normalization", "initialization|lstm|gating"]),
    ("NLP", "Intermediate", "How would you turn raw text into features for a classifier?",
     ["tokeniz|tokenis", "tf-idf|bag of words|embedding", "stop words|stemming|lemmat|clean", "vocabulary|vector"]),
    ("LLMs", "Intermediate", "What is retrieval-augmented generation (RAG) and when is it better than fine-tuning?",
     ["retriev", "context|prompt", "embedding|vector", "hallucinat|up-to-date|knowledge"]),
    ("PyTorch", "Intermediate", "Describe a typical PyTorch training loop.",
     ["forward", "loss", "backward|backprop", "optimizer|step|zero_grad"]),
    # ---- Web / APIs / backend
    ("REST APIs", "Beginner", "What is a REST API and what are the common HTTP methods?",
     ["get", "post", "put|patch", "delete|stateless|status code"]),
    ("REST APIs", "Intermediate", "How would you design authentication and error handling for a REST API?",
     ["token|jwt|oauth|api key", "status code|4xx|5xx", "validation|validate", "https|rate limit"]),
    ("Flask", "Intermediate", "How does Flask handle routing and request context, and how would you structure a larger app?",
     ["route|decorator", "request", "blueprint", "config|factory"]),
    ("FastAPI", "Intermediate", "What advantages does FastAPI offer, and how does it validate requests?",
     ["pydantic|type hint", "async", "openapi|docs|swagger", "validation"]),
    ("JavaScript", "Beginner", "Explain var, let and const and how hoisting works.",
     ["scope", "let|const|block", "hoist", "reassign|immutable|temporal dead zone"]),
    ("JavaScript", "Intermediate", "How do promises and async/await work in JavaScript?",
     ["promise", "async|await", "event loop|non-blocking|callback", "error|catch|try"]),
    ("React", "Intermediate", "What are React hooks and why does state change trigger a re-render?",
     ["usestate|state", "useeffect|effect", "re-render|render", "component|props|virtual dom"]),
    ("HTML", "Beginner", "What is semantic HTML and why does it matter?",
     ["semantic|meaningful", "accessib", "seo", "header|nav|article|section"]),
    ("CSS", "Beginner", "Explain the CSS box model and the difference between flexbox and grid.",
     ["margin", "padding", "border", "flex|grid|one-dimensional|two-dimensional"]),
    ("MongoDB", "Intermediate", "When would you choose MongoDB over a relational database?",
     ["document|json", "schema|flexible", "join|relation", "scal"]),
    ("Docker", "Intermediate", "What problem does Docker solve and what is the difference between an image and a container?",
     ["image", "container", "isolat|environment|dependenc", "dockerfile|portab"]),
    ("Git", "Beginner", "Explain the difference between git merge and git rebase.",
     ["merge", "rebase", "history", "conflict|branch"]),
    ("Testing", "Intermediate", "What makes a good unit test, and how do you decide what to mock?",
     ["isolat|independent", "assert", "mock|stub", "edge case|deterministic|fast"]),
    # ---- CS fundamentals
    ("Data Structures", "Beginner", "What is the difference between an array and a linked list?",
     ["contiguous|index|random access", "pointer|node", "insert|delete", "memory|O(1)|O(n)"]),
    ("Data Structures", "Intermediate", "How does a hash table work and how are collisions handled?",
     ["hash function|hash", "bucket|index", "collision", "chaining|open addressing|probing"]),
    ("Algorithms", "Intermediate", "Explain binary search and its time complexity.",
     ["sorted", "middle|mid|half", "O(log n)|log n|logarithmic", "compare|left|right"]),
    ("Algorithms", "Advanced", "How would you approach a problem you suspect needs dynamic programming?",
     ["overlapping subproblems|subproblem", "optimal substructure", "memoization|memoisation|tabulation|cache", "state|recurrence"]),
    ("OOP", "Beginner", "Explain the four pillars of object-oriented programming with examples.",
     ["encapsulation", "inheritance", "polymorphism", "abstraction"]),
    ("System Design", "Advanced", "How would you design a URL shortener that handles heavy traffic?",
     ["hash|id|base62", "database|storage", "cache", "scal|load balanc|replicat"]),
    ("CI/CD", "Intermediate", "What is CI/CD and what stages would a basic pipeline contain?",
     ["build", "test", "deploy", "automat"]),
    ("Cloud", "Beginner", "What is the difference between IaaS, PaaS and SaaS?",
     ["infrastructure", "platform", "software", "manage|responsib"]),
]

BEHAVIORAL: List[Q] = [
    ("Behavioral", "Beginner", "Tell me about yourself and why you are interested in this role.",
     ["background|education", "skills|projects", "role|interest|motivat", "goal|learn"]),
    ("Behavioral", "Intermediate", "Describe a time you faced a difficult technical problem. How did you approach it?",
     ["situation|context", "task|problem", "action|I did|I decided", "result|outcome|learned"]),
    ("Behavioral", "Intermediate", "Tell me about a disagreement in a team and how you handled it.",
     ["situation|context", "listen|understand", "action|compromise|discuss", "result|outcome"]),
    ("Behavioral", "Intermediate", "Describe a project deadline you were at risk of missing. What did you do?",
     ["prioritiz|prioritis", "communicat", "action|scope|plan", "result|outcome|learned"]),
    ("Behavioral", "Advanced", "Tell me about a time you made a mistake in your work and what you changed afterwards.",
     ["own|responsib|accountab", "fix|action", "learn|process|prevent", "result|outcome"]),
]

_LEVEL_ORDER = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}


def questions_for(skill: str, difficulty: str) -> List[Q]:
    """Questions for ``skill`` at the requested level, then adjacent levels (closest first)."""
    target = _LEVEL_ORDER.get(difficulty, 1)
    items = [q for q in BANK if q[0] == skill]
    return sorted(items, key=lambda q: abs(_LEVEL_ORDER[q[1]] - target))


def behavioral(difficulty: str) -> List[Q]:
    target = _LEVEL_ORDER.get(difficulty, 1)
    return sorted(BEHAVIORAL, key=lambda q: abs(_LEVEL_ORDER[q[1]] - target))


def concepts_by_question() -> Dict[str, List[str]]:
    return {q[2]: q[3] for q in BANK + BEHAVIORAL}
