import asyncio,logging,os,datetime
from typing import Any
from src.domain.memory import MemoryConsolidator
from src.infrastructure.llm import LlmClient
from src.infrastructure.plugin_loader import AgentRegistry, PluginLoader
from src.infrastructure.redis import RedisClient
from src.infrastructure.surrealdb import SurrealDbClient
from src.models.hlink import HLinkMessage,MessageType,Payload,Recipient,Sender
from src.services.visual.dreamer import Dreamer
from src.services.visual.manager import AssetManager
from src.services.visual.provider import NanoBananaProvider
from src.services.chat.commands import CommandHandler
from src.utils.privacy import PrivacyFilter
from agents.electra.drivers.ha_client import HaClient
logging.basicConfig(level=logging.DEBUG,format='%(levelname)s:%(name)s:%(message)s')
logger=logging.getLogger("H-CORE")

class RedisLogHandler(logging.Handler):
    def __init__(self, redis_client):
        super().__init__()
        self.redis = redis_client
        self.setFormatter(logging.Formatter('%(name)s: %(message)s'))

    def emit(self, record):
        try:
            # STORY 25.1: Filter out noisy infrastructure logs
            if "redis" in record.name.lower() or "httpx" in record.name.lower() or "httpcore" in record.name.lower():
                return
                
            msg_str = self.format(record)
            h_msg = HLinkMessage(
                type="system.log",
                sender=Sender(agent_id="core", role="system"),
                recipient=Recipient(target="broadcast"),
                payload=Payload(content=msg_str)
            )
            # Use a fire-and-forget approach or a small queue to avoid blocking logging
            asyncio.create_task(self.redis.publish("broadcast", h_msg))
        except:
            pass

pf,consolidator,vs,dreamer,ha,ch,lh=PrivacyFilter(),None,None,None,None,None,None
sleep_trigger_event=asyncio.Event()
rc=RedisClient(host=os.getenv("REDIS_HOST","localhost"))
sc=SurrealDbClient(
    url=os.getenv("SURREALDB_URL","ws://surrealdb:8000/rpc"),
    user=os.getenv("SURREALDB_USER","root"),
    password=os.getenv("SURREALDB_PASS","root")
)
lc,ar=LlmClient(),AgentRegistry()
pl=PluginLoader(os.getenv("AGENTS_PATH","/app/agents"),ar,rc,lc,sc)
async def router(cmd_h,s_c):
    logger.info("ROUTER: Listening on 'broadcast'...")
    async def handler(msg):
        if msg.type == MessageType.SYSTEM_STATUS_UPDATE:
            try:
                content = msg.payload.content
                if isinstance(content, dict) and content.get("status") == "SLEEP_START":
                    logger.info("ROUTER: Received SLEEP_START signal.")
                    sleep_trigger_event.set()
            except Exception as e:
                logger.error(f"ROUTER: Error handling status update: {e}")

        if msg.type in [MessageType.NARRATIVE_TEXT,MessageType.EXPERT_RESPONSE,MessageType.VISUAL_ASSET]:
            d=msg.model_dump()
            if isinstance(d.get("payload",{}).get("content"),str):
                txt,_=pf.redact(d["payload"]["content"]);d["payload"]["content"]=txt
            # Ensure top level agent_id for simpler querying
            d["agent_id"] = msg.sender.agent_id
            await s_c.persist_message(d)
        if msg.type==MessageType.NARRATIVE_TEXT:
            c=str(msg.payload.content)
            if c.startswith("/"):
                logger.info(f"ROUTER: Triggering slash command: {c}")
                await cmd_h.execute(c,msg)
        elif msg.type==MessageType.EXPERT_COMMAND:
            p=msg.payload.content
            cmd,args=None,""
            if isinstance(p,dict):
                if msg.recipient.target=="outfit":
                    cmd="outfit";ta=p.get("command");oa=p.get("args","");args=f"{ta} {oa}"
                else:cmd=p.get("command");args=p.get("args","")
            if cmd in cmd_h.commands:
                logger.info(f"ROUTER: Intercepted expert /{cmd} {args}")
                await cmd_h.execute(f"/{cmd} {args}",msg)
    await rc.subscribe("broadcast",handler)
async def health():
    while True:
        try:
            if rc.client:
                await rc.publish("broadcast",HLinkMessage(type=MessageType.SYSTEM_STATUS_UPDATE,sender=Sender(agent_id="core",role="system"),recipient=Recipient(target="system"),payload=Payload(content={"component":"redis","status":"ok"})))
                await rc.publish("broadcast",HLinkMessage(type=MessageType.SYSTEM_STATUS_UPDATE,sender=Sender(agent_id="core",role="system"),recipient=Recipient(target="system"),payload=Payload(content={"component":"llm","status":"ok"})))
        except:pass
        await asyncio.sleep(30)
async def heartbeat():
    while True:
        try:
            await rc.publish("broadcast",HLinkMessage(type=MessageType.SYSTEM_STATUS_UPDATE,sender=Sender(agent_id="system",role="orchestrator"),recipient=Recipient(target="system"),payload=Payload(content={"component":"brain","status":"online","active":True,"personified":False,"commands":["imagine","outfit","vault","location"]})))
        except:pass
        await asyncio.sleep(10)
async def sleep_cycle_worker():
    logger.info("WORKER: Sleep cycle orchestration started.")
    last_run = 0
    daily_run_done = False
    
    while True:
        try:
            now = datetime.datetime.now()
            current_ts = now.timestamp()
            
            # Check for forced run via event
            if sleep_trigger_event.is_set():
                logger.info("WORKER: Forced sleep cycle triggered.")
                sleep_trigger_event.clear()
                # Force run logic: treat as if enough time passed
                last_run = 0 
            
            # 1. Hourly Consolidation (Default 3600s)
            # We use a slight buffer to avoid spamming if loop runs fast, but last_run=0 ensures first run.
            if current_ts - last_run >= 3600:
                if consolidator:
                    await consolidator.consolidate()
                    last_run = current_ts
                else:
                    logger.warning("WORKER: Consolidator not initialized yet.")
                
            # 2. Daily Maintenance (3 AM)
            if now.hour == 3:
                if not daily_run_done:
                    logger.info("WORKER: Starting daily deep sleep maintenance...")
                    if consolidator:
                        await consolidator.apply_decay()
                    if dreamer:
                        await dreamer.prepare_daily_assets()
                    daily_run_done = True
            else:
                # Reset flag once we are out of the 3 AM hour
                daily_run_done = False
                
        except Exception as e:
            logger.error(f"WORKER: Sleep cycle error: {e}", exc_info=True)
            
        # Check every minute
        await asyncio.sleep(60)

async def main():
    global consolidator,vs,dreamer,ha,ch,vs
    await rc.connect();await sc.connect()
    
    # STORY 25.1: Start broadcasting logs to UI
    log_handler = RedisLogHandler(rc)
    log_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(log_handler)
    logger.info("SYSTEM: Log broadcasting active.")

    ha=HaClient();from src.services.visual.service import VisualImaginationService
    
    # STORY 25.1: Configurable Visual Provider
    visual_provider_type = os.getenv("VISUAL_PROVIDER", "google").lower()
    if visual_provider_type == "google":
        from src.services.visual.provider import GoogleImagenProvider
        vp = GoogleImagenProvider()
    elif visual_provider_type == "imagen-v2":
        from src.services.visual.provider import ImagenV2Provider
        vp = ImagenV2Provider()
    else:
        vp=NanoBananaProvider()
    
    am=AssetManager(sc);vs=VisualImaginationService(vp,am,lc,rc);dreamer=Dreamer(ha,vs);ch=CommandHandler(rc,vs,sc);pl.visual_service=vs
    consolidator=MemoryConsolidator(sc,lc,rc);await pl.start()
    tasks=[asyncio.create_task(health()),asyncio.create_task(heartbeat()),asyncio.create_task(router(ch,sc)),asyncio.create_task(sleep_cycle_worker())]
    await asyncio.gather(*tasks)
if __name__=="__main__":
    try:asyncio.run(main())
    except Exception as e:logger.critical(f"CRASH: {e}",exc_info=True)
