"""Question Generator — uses Ollama when available, built-in question bank as fallback."""

import json
import random
import httpx

from config import settings
from models import Question, Difficulty


# ── Built-in question bank (fallback) ───────────────────────────────────────

QUESTION_BANK = {
    "Python": {
        "Easy": [
            "What is the difference between a list and a tuple in Python?",
            "Explain the concept of list comprehension in Python with an example.",
            "What are Python decorators and why are they useful?",
            "Explain the difference between '==' and 'is' operators in Python.",
            "What are *args and **kwargs in Python? Provide examples.",
            "What is the difference between a shallow copy and a deep copy?",
            "Explain the Global Interpreter Lock (GIL) in Python.",
            "What are Python generators and how do they differ from regular functions?",
        ],
        "Medium": [
            "Explain Python's memory management and garbage collection mechanism.",
            "What are metaclasses in Python and when would you use them?",
            "Explain the descriptor protocol in Python and give a practical use case.",
            "How does Python's method resolution order (MRO) work with multiple inheritance?",
            "Explain the difference between @staticmethod, @classmethod, and instance methods.",
            "What are context managers in Python? Explain the __enter__ and __exit__ methods.",
            "How would you implement a thread-safe singleton pattern in Python?",
            "Explain how async/await works in Python and when to use it over threading.",
        ],
        "Hard": [
            "Explain Python's C3 linearization algorithm for MRO with a diamond inheritance example.",
            "How would you implement a custom import hook in Python? Describe the finder/loader protocol.",
            "Explain how Python's asyncio event loop works internally, including the role of selectors.",
            "Describe the internals of Python's dictionary implementation and how it handles hash collisions.",
            "How would you profile and optimize a memory-intensive Python application? Discuss tools and techniques.",
            "Explain how CPython garbage collection handles reference cycles using generational GC.",
        ],
    },
    "JavaScript": {
        "Easy": [
            "What is the difference between var, let, and const in JavaScript?",
            "Explain the concept of closures in JavaScript with an example.",
            "What is the event loop in JavaScript and how does it work?",
            "Explain prototypal inheritance in JavaScript.",
            "What are Promises and how do they differ from callbacks?",
            "What is the difference between '==' and '===' in JavaScript?",
        ],
        "Medium": [
            "Explain the JavaScript event delegation pattern and when to use it.",
            "How does the 'this' keyword work in different contexts in JavaScript?",
            "Explain the module pattern and its evolution from IIFE to ES modules.",
            "What are WeakMap and WeakSet? When would you use them over Map and Set?",
            "Explain how JavaScript handles asynchronous operations with the microtask and macrotask queues.",
            "How does garbage collection work in JavaScript engines like V8?",
        ],
        "Hard": [
            "Explain the internals of the V8 engine's compilation pipeline (Ignition + TurboFan).",
            "How would you implement a reactive system similar to Vue.js reactivity using Proxies?",
            "Describe the Structured Clone Algorithm and its limitations compared to JSON serialization.",
            "Explain how SharedArrayBuffer and Atomics enable shared memory parallelism in JavaScript.",
        ],
    },
    "Data Structures & Algorithms": {
        "Easy": [
            "Explain the difference between an array and a linked list. When would you use each?",
            "What is a hash table and how does it handle collisions?",
            "Explain the difference between a stack and a queue with real-world examples.",
            "What is the time complexity of common operations on a binary search tree?",
            "Explain BFS and DFS traversal algorithms and their use cases.",
        ],
        "Medium": [
            "Explain how a self-balancing BST (e.g., AVL tree) maintains balance after insertions.",
            "Describe Dijkstra's algorithm and discuss its time complexity with different data structures.",
            "What is dynamic programming? Explain with the knapsack problem as an example.",
            "How does a trie data structure work and what are its advantages over hash maps for string lookups?",
            "Explain the difference between merge sort and quick sort. When would you prefer one over the other?",
        ],
        "Hard": [
            "Explain the amortized analysis of dynamic array resizing using the aggregate and potential methods.",
            "Describe the B-tree data structure and explain why it's preferred for database indexing over BSTs.",
            "Explain the A* search algorithm and how it differs from Dijkstra's algorithm.",
            "What is a skip list and how does it achieve O(log n) average-case performance?",
            "Explain the Aho-Corasick algorithm and where you'd use it over simpler string matching.",
        ],
    },
    "System Design": {
        "Easy": [
            "Explain the differences between monolithic and microservices architectures.",
            "What is load balancing and what are the common strategies?",
            "Explain the concept of database sharding and when you would use it.",
            "What is caching? Explain different caching strategies (write-through, write-back, write-around).",
        ],
        "Medium": [
            "Design a URL shortening service like bit.ly. Discuss the key components and trade-offs.",
            "How would you design a rate limiter? Discuss different algorithms (token bucket, sliding window).",
            "Explain the CAP theorem and its implications for distributed system design.",
            "How would you design a notification system that handles millions of users?",
        ],
        "Hard": [
            "Design a distributed message queue similar to Apache Kafka. Discuss partitioning, replication, and ordering guarantees.",
            "How would you design a real-time collaborative editing system like Google Docs?",
            "Design a global-scale content delivery network. Discuss consistency, caching invalidation, and edge routing.",
            "How would you design a search engine with type-ahead suggestions handling billions of queries?",
        ],
    },
    "SQL & Databases": {
        "Easy": [
            "What is the difference between SQL and NoSQL databases? When would you choose one over the other?",
            "Explain the different types of SQL JOINs with examples.",
            "What are database indexes and how do they improve query performance?",
            "Explain the ACID properties in the context of database transactions.",
        ],
        "Medium": [
            "Explain database normalization (1NF through 3NF) with practical examples.",
            "What is a database transaction isolation level? Explain the four standard levels.",
            "How does query optimization work in relational databases? Explain the role of the query planner.",
            "What are materialized views and when would you use them?",
        ],
        "Hard": [
            "Explain the MVCC (Multi-Version Concurrency Control) mechanism and how PostgreSQL implements it.",
            "How would you design a database schema for a multi-tenant SaaS application?",
            "Explain the Raft consensus algorithm and how it's used in distributed databases.",
        ],
    },
    "Machine Learning": {
        "Easy": [
            "What is the difference between supervised and unsupervised learning? Give examples of each.",
            "Explain the bias-variance tradeoff in machine learning.",
            "What is overfitting and how can you prevent it?",
            "Explain the difference between precision, recall, and F1-score.",
        ],
        "Medium": [
            "Explain how gradient descent works. What is the difference between batch, mini-batch, and stochastic gradient descent?",
            "What are the key differences between Random Forest and Gradient Boosting?",
            "Explain the attention mechanism in transformers and why it revolutionized NLP.",
            "How does backpropagation work in neural networks? Explain the chain rule's role.",
        ],
        "Hard": [
            "Explain the mathematics behind the transformer architecture, including scaled dot-product attention.",
            "How do GANs (Generative Adversarial Networks) work? Discuss training instability and mitigation strategies.",
            "Explain the RLHF (Reinforcement Learning from Human Feedback) pipeline used to train LLMs.",
        ],
    },
}

# Fallback for topics not in the bank
DEFAULT_QUESTIONS = {
    "Easy": [
        "Explain the fundamental concepts of {topic}.",
        "What are the key differences between common approaches in {topic}?",
        "Describe a basic use case for {topic} and how you would implement it.",
    ],
    "Medium": [
        "Discuss the design patterns commonly used in {topic} and when to apply each.",
        "Explain the performance considerations when working with {topic}.",
        "How would you debug a complex issue in a {topic}-based system?",
    ],
    "Hard": [
        "Discuss the internals of a major tool/framework in {topic} and how it achieves its performance characteristics.",
        "How would you architect a large-scale production system using {topic}? Discuss trade-offs.",
        "Explain an advanced optimization technique in {topic} with real-world implications.",
    ],
}


QUESTION_PROMPT_TEMPLATE = """You are an expert technical interviewer.

Generate ONE technical interview question on the topic: "{topic}"
Difficulty level: {difficulty}

The question should:
- Be clear and specific
- Test real understanding, not just memorization
- Be appropriate for the given difficulty level

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
    "question_text": "Your question here"
}}"""


async def _try_ollama(topic: str, difficulty: Difficulty) -> str | None:
    """Try to generate via Ollama. Returns question text or None on failure."""
    prompt = QUESTION_PROMPT_TEMPLATE.format(topic=topic, difficulty=difficulty.value)
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.8},
                },
            )
            response.raise_for_status()
            data = response.json()
            raw_text = data.get("response", "")
            parsed = json.loads(raw_text)
            return parsed["question_text"]
    except Exception:
        return None


def _pick_from_bank(topic: str, difficulty: str) -> str:
    """Pick a random question from the built-in bank."""
    topic_bank = QUESTION_BANK.get(topic)
    if topic_bank and difficulty in topic_bank:
        return random.choice(topic_bank[difficulty])
    # Fallback generic questions
    templates = DEFAULT_QUESTIONS.get(difficulty, DEFAULT_QUESTIONS["Medium"])
    return random.choice(templates).format(topic=topic)


async def generate_question(
    topic: str,
    difficulty: Difficulty,
    question_id: int = 1,
) -> Question:
    """Generate a question via Ollama; fall back to built-in bank if unavailable."""

    # Try Ollama first
    question_text = await _try_ollama(topic, difficulty)

    # Fallback to bank
    if question_text is None:
        question_text = _pick_from_bank(topic, difficulty.value)

    return Question(
        question_id=question_id,
        topic=topic,
        difficulty=difficulty,
        question_text=question_text,
    )
