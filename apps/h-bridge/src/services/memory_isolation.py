import json
import logging
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class MemoryIsolationService:
    """Service for managing user memory with session-based isolation."""

    def __init__(self, redis_client, surreal_client=None):
        self.redis = redis_client
        self.surreal = surreal_client
        self._user_sessions = {}

    async def initialize(self):
        """Initialize the service."""
        logger.info("MemoryIsolationService initialized")

    def _get_session_key(self, user_id: str, session_id: str) -> str:
        """Get Redis key for user session memory."""
        return f"memory:user:{user_id}:session:{session_id}"

    def _get_user_sessions_key(self, user_id: str) -> str:
        """Get Redis key for user's session list."""
        return f"memory:user:{user_id}:sessions"

    def _get_valid_sessions_key(self, user_id: str) -> str:
        """Get Redis set of valid sessions for a user."""
        return f"memory:user:{user_id}:valid_sessions"

    async def create_user(self, user_id: str, email: str = "", name: str = "", session_id: Optional[str] = None) -> dict[str, Any]:
        """Create a new user."""
        user_key = f"user:{user_id}"
        
        user_data = {
            "id": user_id,
            "email": email,
            "name": name,
            "created_at": str(uuid4())
        }
        
        if self.redis and self.redis.client:
            await self.redis.client.hset(user_key, mapping=user_data)
            await self.redis.client.sadd(self._get_user_sessions_key(user_id), "")
            if session_id:
                await self.redis.client.sadd(self._get_valid_sessions_key(user_id), session_id)
        
        logger.info(f"Created user: {user_id}")
        return user_data

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user and all their session memories."""
        user_key = f"user:{user_id}"
        
        if self.redis and self.redis.client:
            sessions = await self.redis.client.smembers(self._get_user_sessions_key(user_id))
            for session_id in sessions:
                if session_id:
                    await self.redis.client.delete(self._get_session_key(user_id, session_id))
            valid_sessions = await self.redis.client.smembers(self._get_valid_sessions_key(user_id))
            for session_id in valid_sessions:
                if session_id:
                    await self.redis.client.delete(self._get_session_key(user_id, session_id))
            await self.redis.client.delete(self._get_user_sessions_key(user_id))
            await self.redis.client.delete(self._get_valid_sessions_key(user_id))
            await self.redis.client.delete(user_key)
        
        logger.info(f"Deleted user: {user_id}")
        return True

    async def validate_session(self, user_id: str, session_id: str) -> tuple[bool, Optional[str]]:
        """Validate if session belongs to user. Returns (is_valid, error_message)."""
        if not session_id:
            return False, "No session provided"
        
        if not user_id:
            return False, "No user_id provided"
        
        if self.redis and self.redis.client:
            user_key = f"user:{user_id}"
            user_exists = await self.redis.client.exists(user_key)
            if not user_exists:
                return False, "User not found"
            
            valid_sessions = await self.redis.client.smembers(self._get_valid_sessions_key(user_id))
            valid_sessions = set(s.decode() if isinstance(s, bytes) else s for s in valid_sessions if s)
            if session_id in valid_sessions:
                return True, None
            
            # Check if session belongs to a different user
            session_owner_key = f"session_owner:{session_id}"
            owner_user = await self.redis.client.get(session_owner_key)
            if owner_user:
                if isinstance(owner_user, bytes):
                    owner_user = owner_user.decode()
                if owner_user != user_id:
                    return False, "Session does not match user"
            
            # Session doesn't exist or isn't registered - deny access
            return False, "Session not registered"
        
        return True, None

    async def store_memory(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
        memory: Optional[str] = None,
        emotional_context: Optional[dict[str, Any]] = None,
        context: Optional[dict[str, Any]] = None,
        extra_data: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Store memory for a specific user and session."""
        effective_user_id = user_id
        
        if not effective_user_id:
            return {"success": False, "error": "user_id is required"}
        
        effective_session_id = session_id or f"auto_session_{uuid4().hex[:8]}"
        
        if self.redis and self.redis.client:
            user_key = f"user:{effective_user_id}"
            user_exists = await self.redis.client.exists(user_key)
            if not user_exists:
                await self.create_user(effective_user_id, "", "")
            
            await self.redis.client.sadd(self._get_valid_sessions_key(effective_user_id), effective_session_id)
            session_owner_key = f"session_owner:{effective_session_id}"
            await self.redis.client.set(session_owner_key, effective_user_id)
        
        session_key = self._get_session_key(effective_user_id, effective_session_id)
        
        def serialize_value(v):
            if isinstance(v, (dict, list)):
                return json.dumps(v)
            return v
        
        memory_data = {}
        
        # Handle nested data object
        if data:
            for key, value in data.items():
                if key == "data":
                    if isinstance(value, dict):
                        for k, v in value.items():
                            memory_data[k] = serialize_value(v)
                    else:
                        memory_data["data"] = serialize_value(value)
                elif key in ("emotionalContext", "emotional_context"):
                    memory_data["emotionalContext"] = serialize_value(value)
                elif key in ("context", "context"):
                    memory_data["context"] = serialize_value(value)
                elif key not in ("userId", "sessionId"):
                    memory_data[key] = serialize_value(value)
        else:
            if memory:
                memory_data["memory"] = memory
            if emotional_context:
                memory_data["emotionalContext"] = serialize_value(emotional_context)
            if context:
                memory_data["context"] = serialize_value(context)
        
        # Handle extra fields
        if extra_data:
            for key, value in extra_data.items():
                if key not in ("userId", "sessionId"):
                    memory_data[key] = serialize_value(value)
        
        memory_data["userId"] = effective_user_id
        memory_data["sessionId"] = effective_session_id
        memory_data["updated_at"] = str(uuid4())
        
        if self.redis and self.redis.client:
            await self.redis.client.hset(session_key, mapping=memory_data)
            await self.redis.client.sadd(self._get_user_sessions_key(effective_user_id), effective_session_id)
        
        logger.info(f"Stored memory for user {effective_user_id}, session {effective_session_id[:8]}..., data = {memory_data}")
        
        return {"success": True, "userId": effective_user_id, "sessionId": effective_session_id, "data": memory_data.get("data", {})}

    async def get_memory(self, user_id: str, session_id: Optional[str] = None) -> dict[str, Any]:
        """Get memory for a specific user and session with validation."""
        if not session_id:
            return {"userId": user_id, "sessionId": "", "data": {}}
        
        if not user_id:
            return {"error": "unauthorized", "message": "No user_id provided", "status": 401}
        
        is_valid, error = await self.validate_session(user_id, session_id)
        
        if not is_valid:
            if "not found" in error.lower():
                return {"userId": user_id, "sessionId": session_id, "data": {}}
            if "does not match" in error.lower():
                return {"error": "forbidden", "message": error, "status": 403}
            return {"error": "forbidden", "message": error, "status": 403}
        
        session_key = self._get_session_key(user_id, session_id)
        
        result = {"userId": user_id, "sessionId": session_id, "data": {}}
        
        if self.redis and self.redis.client:
            memory_data = await self.redis.client.hgetall(session_key)
            logger.info(f"get_memory: raw memory_data = {memory_data}")
            if memory_data:
                # Handle bytes keys and values
                parsed_data = {}
                for key, value in memory_data.items():
                    # Decode keys
                    if isinstance(key, bytes):
                        key = key.decode()
                    # Handle value
                    if value and isinstance(value, bytes):
                        value = value.decode()
                    if value:
                        try:
                            # Try to parse JSON
                            if value.startswith('{') or value.startswith('['):
                                parsed_data[key] = json.loads(value)
                            else:
                                parsed_data[key] = value
                        except:
                            parsed_data[key] = value
                    else:
                        parsed_data[key] = value
                
                logger.info(f"get_memory: parsed_data = {parsed_data}")
                
                # Remove internal fields
                for field in ["userId", "sessionId"]:
                    parsed_data.pop(field, None)
                
                result["data"] = parsed_data
                logger.info(f"get_memory: result = {result}")
        
        return result

    async def get_emotional_context(self, user_id: str, session_id: str) -> dict[str, Any]:
        """Get emotional context for a specific user and session."""
        if not session_id:
            return {"error": "unauthorized", "message": "No session provided", "status": 401}
        
        if not user_id:
            return {"error": "unauthorized", "message": "No user_id provided", "status": 401}
        
        is_valid, error = await self.validate_session(user_id, session_id)
        
        if not is_valid:
            if "not found" in error.lower():
                return {"error": "not_found", "message": error, "status": 404}
            if "does not match" in error.lower():
                return {"error": "forbidden", "message": error, "status": 403}
        
        session_key = self._get_session_key(user_id, session_id)
        
        if self.redis and self.redis.client:
            emotional_data = await self.redis.client.hget(session_key, "emotionalContext")
            if emotional_data:
                try:
                    if isinstance(emotional_data, str):
                        return json.loads(emotional_data)
                    return emotional_data
                except json.JSONDecodeError:
                    pass
        
        return {"mood": "neutral", "intensity": 0.0}

    async def get_context(self, user_id: str, session_id: str) -> dict[str, Any]:
        """Get context for a specific user and session."""
        if not session_id:
            return {"error": "unauthorized", "message": "No session provided", "status": 401}
        
        if not user_id:
            return {"error": "unauthorized", "message": "No user_id provided", "status": 401}
        
        is_valid, error = await self.validate_session(user_id, session_id)
        
        if not is_valid:
            if "not found" in error.lower():
                return {"error": "not_found", "message": error, "status": 404}
            if "does not match" in error.lower():
                return {"error": "forbidden", "message": error, "status": 403}
        
        session_key = self._get_session_key(user_id, session_id)
        
        if self.redis and self.redis.client:
            context_data = await self.redis.client.hget(session_key, "context")
            if context_data:
                try:
                    if isinstance(context_data, str):
                        return json.loads(context_data)
                    return context_data
                except json.JSONDecodeError:
                    pass
        
        return {}

    async def list_memories(self, user_id: str, session_id: str) -> dict[str, Any]:
        """List all memories for a user (filtered by session if provided)."""
        if not session_id:
            return {"error": "unauthorized", "message": "No session provided", "status": 401}
        
        if not user_id:
            return {"error": "unauthorized", "message": "No user_id provided", "status": 401}
        
        is_valid, error = await self.validate_session(user_id, session_id)
        
        if not is_valid:
            if "not found" in error.lower():
                return {"error": "not_found", "message": error, "status": 404}
            if "does not match" in error.lower():
                return {"error": "forbidden", "message": error, "status": 403}
        
        memories = []
        
        if self.redis and self.redis.client:
            session_keys = await self.redis.client.smembers(self._get_user_sessions_key(user_id))
            for sid in session_keys:
                if sid:
                    session_key = self._get_session_key(user_id, sid)
                    memory_data = await self.redis.client.hgetall(session_key)
                    if memory_data:
                        memory_data.pop("updated_at", None)
                        memories.append({
                            "sessionId": sid,
                            "data": memory_data
                        })
        
        return {"userId": user_id, "memories": memories}
