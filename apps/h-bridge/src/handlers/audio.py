"""
Audio Processing Handler for hAIrem Audio Ingestion Pipeline
Processes incoming audio data and forwards to STT/LLM processing
"""

import asyncio
import base64
import json
import logging
from typing import Dict, Any, Optional
from io import BytesIO

from fastapi import WebSocket
from models.hlink import HLinkMessage, MessageType, Payload, Sender, Recipient

logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.active_sessions = {}  # Track user recording sessions
        
    async def process_audio_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Process incoming audio from frontend and forward to STT pipeline."""
        try:
            audio_data = message.get('payload', {}).get('content')
            audio_format = message.get('payload', {}).get('format', 'webm')
            sample_rate = message.get('payload', {}).get('sample_rate', 16000)
            duration = message.get('payload', {}).get('duration')
            
            if not audio_data:
                raise ValueError("No audio content in message")
            
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_data)
            
            # Create processing request for STT
            # STORY 14.1 FIX: Ensure all data is JSON serializable
            processing_message = {
                'type': 'audio_processing_request',
                'sender': {'agent_id': 'audio_bridge', 'role': 'processor'},
                'recipient': {'target': 'whisper_worker'},
                'payload': {
                    'audio_data': audio_bytes.hex(),
                    'format': audio_format,
                    'sample_rate': sample_rate,
                    'source': 'user_microphone',
                    'session_id': message.get('id', 'default')
                }
            }
            
            # Send to Redis stream for Whisper processing
            await self.redis_client.publish_event("audio_stream", processing_message)
            
            # Acknowledge receipt to frontend
            ack_message = HLinkMessage(
                type=MessageType.AUDIO_RECEIVED,
                sender=Sender(agent_id="audio_processor", role="system"),
                recipient=Recipient(target="a2ui"),
                payload=Payload(
                    content=f"Audio received: {len(audio_bytes)} bytes",
                    format=audio_format,
                    status="processing",
                    sample_rate=sample_rate
                )
            )
            
            await websocket.send_text(ack_message.model_dump_json())
            logger.info(f"Audio processing started for session")
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            
            # Send error to frontend
            error_message = HLinkMessage(
                type=MessageType.AUDIO_ERROR,
                sender=Sender(agent_id="audio_processor", role="system"),
                recipient=Recipient(target="a2ui"),
                payload=Payload(
                    content=f"Audio processing error: {str(e)}",
                    error_type="processing_error"
                )
            )
            
            await websocket.send_text(error_message.model_dump_json())
    
    async def handle_stt_result(self, stt_text: str, websocket: WebSocket):
        """Handle STT result and forward as user message to LLM."""
        try:
            # Create user message from transcribed text
            user_message = HLinkMessage(
                type=MessageType.USER_MESSAGE,
                sender=Sender(agent_id="user", role="user"),
                recipient=Recipient(target="llm_router"),
                payload=Payload(
                    content=stt_text,
                    format="text",
                    source="voice_input"
                )
            )
            
            # Send to LLM for processing
            await self.redis_client.publish_event("conversation_stream", "user_message", user_message.model_dump())
            
            # Acknowledge to frontend
            ack_message = HLinkMessage(
                type=MessageType.STT_COMPLETE,
                sender=Sender(agent_id="audio_processor", role="system"),
                recipient=Recipient(target="a2ui"),
                payload=Payload(
                    content=f"Transcription complete: {len(stt_text)} characters",
                    status="transcribed"
                )
            )
            
            await websocket.send_text(ack_message.model_dump_json())
            logger.info(f"STT completed: {stt_text[:50]}...")
            
        except Exception as e:
            logger.error(f"STT handling failed: {e}")
    
    async def handle_session_management(self, websocket: WebSocket, action: str, data: Dict[str, Any]):
        """Handle audio session management (start, stop, status)."""
        try:
            session_id = data.get('session_id')
            
            if action == 'start_session':
                self.active_sessions[session_id] = {
                    'started_at': asyncio.get_event_loop().time(),
                    'status': 'active'
                }
                
                response = HLinkMessage(
                    type=MessageType.AUDIO_SESSION_RESPONSE,
                    sender=Sender(agent_id="audio_processor", role="system"),
                    recipient=Recipient(target="a2ui"),
                    payload=Payload(
                        content="Audio session started",
                        session_id=session_id,
                        status="active"
                    )
                )
                
            elif action == 'stop_session':
                if session_id in self.active_sessions:
                    session = self.active_sessions[session_id]
                    session['stopped_at'] = asyncio.get_event_loop().time()
                    session['status'] = 'stopped'
                
                response = HLinkMessage(
                    type=MessageType.AUDIO_SESSION_RESPONSE,
                    sender=Sender(agent_id="audio_processor", role="system"),
                    recipient=Recipient(target="a2ui"),
                    payload=Payload(
                        content="Audio session stopped",
                        session_id=session_id,
                        status="stopped",
                        duration=session.get('duration') if session else None
                    )
                )
                
            elif action == 'get_status':
                status = self.active_sessions.get(session_id, {}).get('status', 'inactive')
                
                response = HLinkMessage(
                    type=MessageType.AUDIO_SESSION_RESPONSE,
                    sender=Sender(agent_id="audio_processor", role="system"),
                    recipient=Recipient(target="a2ui"),
                    payload=Payload(
                        content=f"Audio session status: {status}",
                        session_id=session_id,
                        status=status
                    )
                )
            
            else:
                raise ValueError(f"Unknown session action: {action}")
            
            await websocket.send_text(response.model_dump_json())
            logger.info(f"Session management: {action} for session {session_id}")
            
        except Exception as e:
            logger.error(f"Session management failed: {e}")


# Audio processing handler function
async def handle_audio_message(websocket: WebSocket, message: Dict[str, Any], redis_client):
    """Main entry point for audio message processing."""
    processor = AudioProcessor(redis_client)
    
    try:
        message_type = message.get('type')
        
        if message_type == 'user_audio':
            await processor.process_audio_message(websocket, message)
        elif message_type == 'audio_session_request':
            await processor.handle_session_management(websocket, 'start_session', message.get('payload', {}))
        elif message_type == 'audio_session_stop':
            await processor.handle_session_management(websocket, 'stop_session', message.get('payload', {}))
        elif message_type == 'audio_session_status':
            await processor.handle_session_management(websocket, 'get_status', message.get('payload', {}))
        else:
            logger.warning(f"Unknown audio message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Audio message handling failed: {e}")
        
        # Send error response
        error_message = HLinkMessage(
            type=MessageType.AUDIO_ERROR,
            sender=Sender(agent_id="audio_processor", role="system"),
            recipient=Recipient(target="a2ui"),
            payload=Payload(
                content=f"Audio processing error: {str(e)}",
                error_type="message_handling_error"
            )
        )
        
        await websocket.send_text(error_message.model_dump_json())