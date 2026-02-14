import re
from typing import Any
from .models import AgentProfile


class TopicExtractor:
    STOP_WORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "under", "again", "further", "then", "once", "here",
        "there", "when", "where", "why", "how", "all", "each", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only", "own",
        "same", "so", "than", "too", "very", "just", "and", "but", "if", "or",
        "because", "until", "while", "this", "that", "these", "those", "what",
        "which", "who", "whom", "its", "it", "i", "you", "he", "she", "we", "they",
        "me", "him", "her", "us", "them", "my", "your", "his", "our", "their",
        "want", "like", "know", "think", "make", "get", "tell", "try", "call",
        "look", "seem", "give", "show", "find", "say", "want", "use", "now",
    }

    DOMAIN_KEYWORDS = {
        "tech": ["python", "javascript", "code", "programming", "software", "api", "database", "web", "computer"],
        "music": ["music", "song", "audio", "sound", "melody", "rhythm", "songwriting", "band", "concert"],
        "art": ["art", "painting", "drawing", "design", "creative", "visual", "image", "photo", "gallery"],
        "science": ["science", "research", "experiment", "physics", "chemistry", "biology", "data", "analysis"],
        "cooking": ["cook", "recipe", "food", "kitchen", "chef", "baking", "dinner", "lunch", "breakfast"],
        "fitness": ["fitness", "workout", "exercise", "gym", "health", "sport", "training", "run", "yoga"],
        "travel": ["travel", "trip", "vacation", "destination", "flight", "hotel", "explore", "adventure"],
        "gaming": ["game", "gaming", "play", "video", "player", "level", "score", "controller"],
        "business": ["business", "meeting", "project", "strategy", "company", "startup", "entrepreneur", "money"],
        "news": ["news", "article", "report", "journalism", "media", "breaking", "headline", "update"],
    }

    def __init__(self, min_word_length: int = 3):
        self.min_word_length = min_word_length

    def extract_keywords(self, text: str) -> list[str]:
        text_lower = text.lower()
        words = re.findall(r'\b[a-z]+\b', text_lower)
        keywords = [
            w for w in words
            if len(w) >= self.min_word_length and w not in self.STOP_WORDS
        ]
        return list(set(keywords))

    def extract_topics(self, text: str) -> list[str]:
        keywords = self.extract_keywords(text)
        topics = []

        for category, domain_words in self.DOMAIN_KEYWORDS.items():
            for keyword in keywords:
                if keyword in domain_words:
                    topics.append(category)

        for keyword in keywords:
            if keyword not in [d for words in self.DOMAIN_KEYWORDS.values() for d in words]:
                topics.append(keyword)

        return list(set(topics))

    def extract_ngrams(self, text: str, n: int = 2) -> list[str]:
        words = self.extract_keywords(text)
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i:i+n])
            ngrams.append(ngram)
        return ngrams


class InterestScorer:
    def __init__(
        self,
        topic_weight: float = 0.4,
        skill_weight: float = 0.35,
        domain_weight: float = 0.25,
    ):
        self.topic_weight = topic_weight
        self.skill_weight = skill_weight
        self.domain_weight = domain_weight

    def calculate_topic_score(
        self,
        agent: AgentProfile,
        extracted_topics: list[str],
    ) -> float:
        if not extracted_topics or not agent.interests:
            return 0.0

        agent_interests_lower = [i.lower() for i in agent.interests]
        matches = sum(1 for topic in extracted_topics if topic.lower() in agent_interests_lower)

        return min(matches / len(agent.interests), 1.0)

    def calculate_skill_score(
        self,
        agent: AgentProfile,
        extracted_keywords: list[str],
    ) -> float:
        if not extracted_keywords or not agent.expertise:
            return 0.0

        agent_expertise_lower = [e.lower() for e in agent.expertise]
        matches = sum(1 for kw in extracted_keywords if kw in agent_expertise_lower)

        return min(matches / len(agent.expertise), 1.0)

    def calculate_domain_score(
        self,
        agent: AgentProfile,
        extracted_topics: list[str],
    ) -> float:
        if not extracted_topics or not agent.domains:
            return 0.0

        agent_domains_lower = [d.lower() for d in agent.domains]
        matches = sum(1 for topic in extracted_topics if topic.lower() in agent_domains_lower)

        return min(matches / len(agent.domains), 1.0)

    def calculate_interest_score(
        self,
        agent: AgentProfile,
        message_content: str,
    ) -> float:
        extractor = TopicExtractor()
        keywords = extractor.extract_keywords(message_content)
        topics = extractor.extract_topics(message_content)

        topic_score = self.calculate_topic_score(agent, topics)
        skill_score = self.calculate_skill_score(agent, keywords)
        domain_score = self.calculate_domain_score(agent, topics)

        return (
            topic_score * self.topic_weight
            + skill_score * self.skill_weight
            + domain_score * self.domain_weight
        )
