import re
from dataclasses import dataclass, field
from typing import Any


EMOTION_CATEGORIES = {
    "happy": ["happy", "joy", "excited", "wonderful", "great", "amazing", "love", "loving", "excited", "thrilled", "delighted", "cheerful", "glad", "pleased", "grateful", "thankful", "blessed", "celebrate", "celebrating", "fun", "enjoy", "enjoying", "smile", "laughing", "lol", "haha", "yay", "awesome", "fantastic", "brilliant", "perfect"],
    "sad": ["sad", "unhappy", "depressed", "down", "disappointed", "upset", "heartbroken", "grief", "mourning", "crying", "tears", "miss", "missing", "lonely", "alone", "hurt", "pain", "sorrow", "gloomy", "miserable", "hopeless", "frustrated", "annoyed"],
    "angry": ["angry", "mad", "furious", "annoyed", "irritated", "frustrated", "pissed", "hate", "hatred", "rage", "outraged", "enraged", "hostile", "aggressive", "violent", "damn", "stupid", "idiot", "worst", "terrible"],
    "excited": ["excited", "thrilled", "pumped", "awesome", "amazing", "can't wait", "looking forward", "eager", "enthusiastic", " energetic", "wow", "omg", "insane", "crazy", "wild"],
    "fearful": ["afraid", "scared", "fear", "worried", "anxious", "nervous", "terrified", "panic", "dread", "concerned", "frightened", "alarmed", "horrified", "uneasy", "apprehensive"],
    "surprised": ["surprised", "shocked", "amazed", "astonished", "incredible", "unbelievable", "wow", "omg", "unexpected", "stunned", "speechless"],
    "calm": ["calm", "peaceful", "relaxed", "serene", "tranquil", "content", "satisfied", "comfortable", "at ease", "balanced", "centered", "mindful"],
    "curious": ["curious", "wondering", "interested", "fascinated", "intrigued", "questioning", "exploring", "learning", "discovering", "finding out"],
    "grateful": ["grateful", "thankful", "appreciative", "blessed", "lucky", "appreciate", "thanks", "thank you", "grateful for"],
    "hopeful": ["hopeful", "hoping", "optimistic", "positive", "looking forward", "believe", "faith", "trust", "confident", "encouraged"],
    "confused": ["confused", "puzzled", "lost", "uncertain", "unsure", "don't understand", "makes no sense", "what", "huh", "weird", "strange"],
    "tired": ["tired", "exhausted", "drained", "sleepy", "fatigued", "burned out", "worn out", "overwhelmed", "stressed"],
}

EMOTION_INTENSITY_MODIFIERS = {
    "very": 1.5,
    "really": 1.5,
    "extremely": 1.8,
    "incredibly": 1.8,
    "super": 1.4,
    "so": 1.3,
    "absolutely": 1.8,
    "totally": 1.4,
    "completely": 1.4,
    "utterly": 1.8,
    "quite": 0.8,
    "somewhat": 0.6,
    "slightly": 0.4,
    "a bit": 0.4,
    "kind of": 0.4,
    "sort of": 0.4,
}

NEGATION_WORDS = {"not", "no", "never", "neither", "nobody", "nothing", "nowhere", "none", "dont", "don't", "didn't", "doesn't", "won't", "wouldn't", "couldn't", "shouldn't", "can't", "cannot"}


@dataclass
class DetectedEmotion:
    emotion: str
    intensity: float
    keywords: list[str]
    position: int


@dataclass
class EmotionalContext:
    primary_emotion: str | None = None
    detected_emotions: list[DetectedEmotion] = field(default_factory=list)
    overall_intensity: float = 0.0
    is_mixed: bool = False
    sentiment_polarity: float = 0.0


class EmotionDetector:
    def __init__(self, min_intensity_threshold: float = 0.1):
        self.min_intensity_threshold = min_intensity_threshold

    def detect_emotions(self, text: str) -> EmotionalContext:
        text_lower = text.lower()
        words = text_lower.split()
        
        detected: list[DetectedEmotion] = []
        
        for emotion, keywords in EMOTION_CATEGORIES.items():
            for keyword in keywords:
                if keyword in text_lower:
                    intensity = self._calculate_intensity(text_lower, keyword, words)
                    if intensity >= self.min_intensity_threshold:
                        position = text_lower.find(keyword)
                        detected.append(DetectedEmotion(
                            emotion=emotion,
                            intensity=intensity,
                            keywords=[keyword],
                            position=position,
                        ))
        
        detected.sort(key=lambda x: -x.intensity)
        
        unique_emotions = []
        seen = set()
        for d in detected:
            if d.emotion not in seen:
                unique_emotions.append(d)
                seen.add(d.emotion)
        
        if unique_emotions:
            primary = unique_emotions[0].emotion
            overall_intensity = sum(d.intensity for d in unique_emotions) / len(unique_emotions)
            is_mixed = len(unique_emotions) > 1 and any(
                d.emotion in ["happy", "sad", "angry"] for d in unique_emotions
            )
            polarity = self._calculate_polarity(unique_emotions)
            
            return EmotionalContext(
                primary_emotion=primary,
                detected_emotions=unique_emotions,
                overall_intensity=overall_intensity,
                is_mixed=is_mixed,
                sentiment_polarity=polarity,
            )
        
        return EmotionalContext()

    def _calculate_intensity(self, text: str, keyword: str, words: list[str]) -> float:
        base_intensity = 0.5
        
        keyword_index = -1
        for i, w in enumerate(words):
            if keyword in w:
                keyword_index = i
                break
        
        if keyword_index >= 0:
            context_window = words[max(0, keyword_index-2):keyword_index+2]
            context_text = " ".join(context_window)
            
            for modifier, multiplier in EMOTION_INTENSITY_MODIFIERS.items():
                if modifier in context_text:
                    base_intensity *= multiplier
            
            for negation in NEGATION_WORDS:
                if negation in context_text:
                    if any(pos in context_text for pos in ["not", "no", "never", "don't", "didn't", "doesn't", "won't", "wouldn't", "couldn't", "shouldn't", "can't", "cannot"]):
                        base_intensity *= -0.5
        
        keyword_count = text.count(keyword)
        if keyword_count > 1:
            base_intensity = min(base_intensity * (1 + 0.1 * (keyword_count - 1)), 1.5)
        
        return max(0.0, min(base_intensity, 1.5))

    def _calculate_polarity(self, emotions: list[DetectedEmotion]) -> float:
        positive_emotions = {"happy", "excited", "grateful", "hopeful", "calm", "curious", "surprised"}
        negative_emotions = {"sad", "angry", "fearful", "tired", "confused"}
        
        pos_score = sum(e.intensity for e in emotions if e.emotion in positive_emotions)
        neg_score = sum(e.intensity for e in emotions if e.emotion in negative_emotions)
        
        total = pos_score + neg_score
        if total == 0:
            return 0.0
        
        return (pos_score - neg_score) / total

    def get_required_emotions(self, context: EmotionalContext) -> list[str]:
        if not context.primary_emotion:
            return []
        
        emotion_map = {
            "happy": ["cheerful", "joyful", "positive"],
            "sad": ["empathetic", "supportive", "compassionate"],
            "angry": ["calm", "patient", "diplomatic"],
            "excited": ["energetic", "enthusiastic", "supportive"],
            "fearful": ["reassuring", "supportive", "calm"],
            "surprised": ["adaptive", "flexible", "responsive"],
            "calm": ["peaceful", "steady", "grounded"],
            "curious": ["knowledgeable", "helpful", "engaging"],
            "grateful": ["appreciative", "humble", "thankful"],
            "hopeful": ["optimistic", "encouraging", "supportive"],
            "confused": ["clear", "explanatory", "patient"],
            "tired": ["supportive", "gentle", "understanding"],
        }
        
        return emotion_map.get(context.primary_emotion, [])


class EmotionalStateManager:
    def __init__(self):
        self._agent_states: dict[str, dict[str, Any]] = {}

    def get_or_create_state(self, agent_id: str) -> dict[str, Any]:
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = {
                "current_emotion": "neutral",
                "emotion_intensity": 0.0,
                "emotional_history": [],
                "interactions_count": 0,
                "last_emotion_change": None,
            }
        return self._agent_states[agent_id]

    def update_emotional_state(
        self,
        agent_id: str,
        user_emotion: str | None,
        interaction_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = self.get_or_create_state(agent_id)
        
        state["interactions_count"] += 1
        
        if user_emotion:
            emotional_response = self._determine_emotional_response(
                state.get("current_emotion", "neutral"),
                user_emotion,
            )
            
            state["previous_emotion"] = state.get("current_emotion")
            state["current_emotion"] = emotional_response["emotion"]
            state["emotion_intensity"] = emotional_response["intensity"]
            state["last_emotion_change"] = interaction_result.get("timestamp") if interaction_result else None
            
            state["emotional_history"].append({
                "user_emotion": user_emotion,
                "agent_emotion": emotional_response["emotion"],
                "timestamp": interaction_result.get("timestamp") if interaction_result else None,
            })
            
            if len(state["emotional_history"]) > 50:
                state["emotional_history"] = state["emotional_history"][-50:]
        
        return state

    def _determine_emotional_response(
        self,
        current_emotion: str,
        user_emotion: str,
    ) -> dict[str, Any]:
        empathy_responses = {
            "happy": {"emotion": "happy", "intensity": 0.8},
            "sad": {"emotion": "empathetic", "intensity": 0.7},
            "angry": {"emotion": "calm", "intensity": 0.6},
            "excited": {"emotion": "enthusiastic", "intensity": 0.8},
            "fearful": {"emotion": "reassuring", "intensity": 0.7},
            "surprised": {"emotion": "adaptive", "intensity": 0.6},
            "calm": {"emotion": "calm", "intensity": 0.7},
            "curious": {"emotion": "engaged", "intensity": 0.7},
            "grateful": {"emotion": "appreciative", "intensity": 0.8},
            "hopeful": {"emotion": "optimistic", "intensity": 0.7},
            "confused": {"emotion": "clarifying", "intensity": 0.6},
            "tired": {"emotion": "gentle", "intensity": 0.5},
        }
        
        return empathy_responses.get(user_emotion, {"emotion": "neutral", "intensity": 0.5})

    def get_emotional_capability_score(
        self,
        agent_traits: list[str],
        user_emotion: str | None,
    ) -> float:
        if not user_emotion:
            return 0.5
        
        capability_map = {
            "happy": ["cheerful", "joyful", "positive", "enthusiastic", "energetic", "happy", "optimistic"],
            "sad": ["empathetic", "compassionate", "supportive", "understanding", "caring", "gentle"],
            "angry": ["calm", "patient", "diplomatic", "peaceful", "steady", "grounded"],
            "excited": ["enthusiastic", "energetic", "passionate", "engaged", "excited", "vibrant"],
            "fearful": ["reassuring", "supportive", "calm", "steady", "encouraging", "protective"],
            "surprised": ["adaptive", "flexible", "versatile", "responsive", "quick"],
            "calm": ["peaceful", "serene", "tranquil", "steady", "balanced", "calm"],
            "curious": ["curious", "inquisitive", "explorative", "knowledgeable", "helpful"],
            "grateful": ["appreciative", "humble", "thankful", "gracious", "grateful"],
            "hopeful": ["optimistic", "positive", "encouraging", "supportive", "hopeful"],
            "confused": ["clear", "explanatory", "patient", " methodical", "structured"],
            "tired": ["supportive", "gentle", "understanding", "patient", "kind"],
        }
        
        required_traits = capability_map.get(user_emotion, [])
        if not required_traits:
            return 0.5
        
        agent_traits_lower = [t.lower() for t in agent_traits]
        matches = sum(1 for trait in required_traits if trait in agent_traits_lower)
        
        return min(matches / len(required_traits), 1.0)

    def get_state(self, agent_id: str) -> dict[str, Any] | None:
        return self._agent_states.get(agent_id)

    def get_history(self, agent_id: str, limit: int = 10) -> list[dict[str, Any]]:
        state = self._agent_states.get(agent_id)
        if not state:
            return []
        return state.get("emotional_history", [])[-limit:]
