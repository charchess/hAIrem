import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

logger = logging.getLogger(__name__)


class TurnState(str, Enum):
    IDLE = "idle"
    RESPONDING = "responding"
    QUEUED = "queued"


@dataclass
class TurnTimeoutConfig:
    default_timeout: float = 30.0
    min_timeout: float = 5.0
    max_timeout: float = 120.0
    warning_threshold: float = 0.8


@dataclass
class QueuedResponse:
    agent_id: str
    message_content: str
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)
    priority: int = 0

    def __lt__(self, other: "QueuedResponse") -> bool:
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.timestamp < other.timestamp


class TurnManager:
    def __init__(
        self,
        redis_client: Optional[Any] = None,
        timeout_config: Optional[TurnTimeoutConfig] = None,
    ):
        self.redis = redis_client
        self.timeout_config = timeout_config or TurnTimeoutConfig()
        
        self._state = TurnState.IDLE
        self._current_agent: Optional[str] = None
        self._response_queue: list[QueuedResponse] = []
        self._turn_start_time: Optional[float] = None
        self._timeout_task: Optional[asyncio.Task] = None
        self._timeout_callback: Optional[Callable[[], Coroutine[Any, Any, None]]] = None
        self._lock = asyncio.Lock()
        
        self._stream_name = "turn_management"
        self._queue_key = "turn_queue"

    @property
    def state(self) -> TurnState:
        return self._state

    @property
    def current_agent(self) -> Optional[str]:
        return self._current_agent

    @property
    def queue_size(self) -> int:
        return len(self._response_queue)

    def set_timeout_callback(self, callback: Callable[[], Coroutine[Any, Any, None]]) -> None:
        self._timeout_callback = callback

    async def request_turn(
        self,
        agent_id: str,
        message_content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        async with self._lock:
            if self._state == TurnState.IDLE:
                await self._start_turn(agent_id, message_content, metadata)
                return True
            elif self._state == TurnState.RESPONDING:
                if agent_id == self._current_agent:
                    logger.debug(f"Agent {agent_id} is already responding")
                    return True
                await self._queue_response(agent_id, message_content, metadata)
                return False
            elif self._state == TurnState.QUEUED:
                await self._queue_response(agent_id, message_content, metadata)
                return False
            return False

    async def _start_turn(
        self,
        agent_id: str,
        message_content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        self._state = TurnState.RESPONDING
        self._current_agent = agent_id
        self._turn_start_time = time.time()
        logger.info(f"Turn started: Agent {agent_id} is now responding")
        
        if self.redis:
            await self.redis.publish_event(
                self._stream_name,
                {
                    "event": "turn_started",
                    "agent_id": agent_id,
                    "timestamp": self._turn_start_time,
                }
            )
        
        self._start_timeout_timer()

    async def _queue_response(
        self,
        agent_id: str,
        message_content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        queued = QueuedResponse(
            agent_id=agent_id,
            message_content=message_content,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        self._response_queue.append(queued)
        self._response_queue.sort()
        
        self._state = TurnState.QUEUED
        
        logger.info(f"Agent {agent_id} queued (queue size: {len(self._response_queue)})")
        
        if self.redis:
            await self.redis.publish_event(
                self._stream_name,
                {
                    "event": "agent_queued",
                    "agent_id": agent_id,
                    "queue_size": len(self._response_queue),
                }
            )

    def _start_timeout_timer(self) -> None:
        if self._timeout_task:
            self._timeout_task.cancel()
        
        timeout = self.timeout_config.default_timeout
        self._timeout_task = asyncio.create_task(self._timeout_handler(timeout))

    async def _timeout_handler(self, timeout: float) -> None:
        try:
            await asyncio.sleep(timeout)
            await self._handle_timeout()
        except asyncio.CancelledError:
            pass

    async def _handle_timeout(self) -> None:
        async with self._lock:
            if self._state != TurnState.RESPONDING:
                return
            
            logger.warning(f"Turn timeout for agent {self._current_agent}")
            
            if self._timeout_callback:
                try:
                    await self._timeout_callback()
                except Exception as e:
                    logger.error(f"Timeout callback failed: {e}")
            
            await self._release_turn(timeout_triggered=True)

    async def release_turn(self) -> None:
        async with self._lock:
            await self._release_turn(timeout_triggered=False)

    async def _release_turn(self, timeout_triggered: bool) -> None:
        previous_agent = self._current_agent
        
        if self._response_queue:
            next_response = self._response_queue.pop(0)
            self._current_agent = next_response.agent_id
            self._turn_start_time = time.time()
            self._state = TurnState.RESPONDING
            
            logger.info(f"Turn transferred to: Agent {self._current_agent}")
            
            if self.redis:
                await self.redis.publish_event(
                    self._stream_name,
                    {
                        "event": "turn_transferred",
                        "previous_agent": previous_agent,
                        "new_agent": self._current_agent,
                        "queue_size": len(self._response_queue),
                    }
                )
            
            self._start_timeout_timer()
        else:
            self._state = TurnState.IDLE
            self._current_agent = None
            self._turn_start_time = None
            
            logger.info("Turn released: No more queued agents")
            
            if self.redis:
                await self.redis.publish_event(
                    self._stream_name,
                    {
                        "event": "turn_released",
                        "previous_agent": previous_agent,
                    }
                )

    async def cancel_turn(self, agent_id: str) -> bool:
        async with self._lock:
            if self._current_agent == agent_id:
                logger.info(f"Cancelling turn for agent {agent_id}")
                if self._timeout_task:
                    self._timeout_task.cancel()
                await self._release_turn(timeout_triggered=False)
                return True
            
            for i, queued in enumerate(self._response_queue):
                if queued.agent_id == agent_id:
                    self._response_queue.pop(i)
                    logger.info(f"Removed queued response for agent {agent_id}")
                    if self.redis:
                        await self.redis.publish_event(
                            self._stream_name,
                            {
                                "event": "queued_response_cancelled",
                                "agent_id": agent_id,
                                "queue_size": len(self._response_queue),
                            }
                        )
                    return True
            return False

    async def get_queue_status(self) -> dict[str, Any]:
        async with self._lock:
            elapsed = 0.0
            if self._turn_start_time:
                elapsed = time.time() - self._turn_start_time
            
            warning_threshold = self.timeout_config.default_timeout * self.timeout_config.warning_threshold
            is_warning = elapsed >= warning_threshold
            
            return {
                "state": self._state.value,
                "current_agent": self._current_agent,
                "queue_size": len(self._response_queue),
                "queued_agents": [q.agent_id for q in self._response_queue],
                "turn_elapsed": elapsed,
                "timeout_warning": is_warning,
            }

    async def force_state(self, state: TurnState) -> None:
        async with self._lock:
            if self._timeout_task:
                self._timeout_task.cancel()
            
            self._state = state
            
            if state == TurnState.IDLE:
                self._current_agent = None
                self._response_queue.clear()
                self._turn_start_time = None
            
            logger.warning(f"Turn state forced to: {state}")

    def set_timeout(self, timeout: float) -> None:
        timeout = max(self.timeout_config.min_timeout, min(timeout, self.timeout_config.max_timeout))
        self.timeout_config.default_timeout = timeout
        logger.info(f"Turn timeout set to: {timeout}s")

    async def clear_queue(self) -> int:
        async with self._lock:
            cleared = len(self._response_queue)
            self._response_queue.clear()
            logger.info(f"Cleared {cleared} queued responses")
            return cleared
