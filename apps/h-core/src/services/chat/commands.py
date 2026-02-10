import hashlib
import logging
from src.models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender

logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self, redis_client, visual_service, surreal_client=None):
        self.redis = redis_client
        self.visual = visual_service
        self.surreal = surreal_client
        self.commands = {
            "imagine": self._run_imagine,
            "outfit": self._run_outfit,
            "location": self._run_location,
            "vault": self._run_vault,
            "ping": self._run_ping
        }

    async def execute(self, command_line: str, original_msg: HLinkMessage):
        parts = command_line.strip().split(" ", 2)
        cmd_name = parts[0].lstrip("/")
        
        if cmd_name in self.commands:
            # Handle case where user just types /imagine or /outfit without agent name
            # We use the original sender if it's a specific agent, or a default
            args = parts[1:] if len(parts) > 1 else []
            await self.commands[cmd_name](args, original_msg)
            return True
        else:
            logger.warning(f"Unknown command: {cmd_name}")
            return False

    async def _run_ping(self, args: list[str], msg: HLinkMessage):
        await self._send_ack(msg, "pong 🏓")

    async def _run_imagine(self, args: list[str], msg: HLinkMessage):
        prompt = " ".join(args)
        if not prompt:
            await self._send_ack(msg, "❌ Précisez ce que je dois imaginer.")
            return
        
        await self._send_ack(msg, f"🎨 J'imagine... *{prompt}*")
        try:
            await self.visual.generate_and_index(
                agent_id="system",
                prompt=prompt,
                tags=["user_requested", "slash_command"],
                asset_type="background"
            )
        except Exception as e:
            await self._send_ack(msg, f"❌ Désolé, l'imagination a échoué: {e}")

    async def _run_outfit(self, args: list[str], msg: HLinkMessage):
        if not args:
            await self._send_ack(msg, "❌ Usage: /outfit [nom_agent] [description]")
            return

        # Smart Parsing: Check if first arg is a known agent
        target_agent = args[0]
        description = " ".join(args[1:]) if len(args) > 1 else ""
        
        # If the first word isn't an agent name, maybe they forgot it?
        # Check against character vault (simplified check)
        known_agents = ["lisa", "renarde", "electra", "dieu"]
        if target_agent.lower() not in known_agents:
            # Shift args: use the whole line as description for the last agent spoken?
            # For now, default to Renarde if unknown
            description = " ".join(args)
            target_agent = "Renarde"

        await self._send_ack(msg, f"👗 Je change la tenue de {target_agent} pour : *{description}*...")
        
        # STORY 25.7: Check Vault
        vault_item = await self.visual.vault.get_item(target_agent, description, category="garment")
        if vault_item:
            logger.info(f"VAULT_HIT: Found garment '{description}' for {target_agent}")
            asset_uri = vault_item["asset"]["url"]
            # Update state with exact vault name
            if self.surreal:
                 await self.surreal.update_agent_state(target_agent, "WEARS", {"name": description, "description": description})
            
            # Notify Visual Asset (Reuse)
            await self.visual.notify_visual_asset(asset_uri, description, target_agent, "pose")
            return

        # 1. Update Graph State (Transient Memory)
        if self.surreal:
             try:
                 # Create target data
                 desc_hash = hashlib.md5(description.encode()).hexdigest()[:8]
                 target_data = {
                     "id": f"outfit_{desc_hash}",
                     "name": f"outfit_{desc_hash}",
                     "description": description
                 }
                 await self.surreal.update_agent_state(target_agent, "WEARS", target_data)

                 # 2. Notify Agent (System Message)
                 notification = HLinkMessage(
                    type=MessageType.NARRATIVE_TEXT, 
                    sender=Sender(agent_id="system", role="orchestrator"),
                    recipient=Recipient(target=target_agent),
                    payload=Payload(content=f"[SYSTEM] Your state updated: You are now wearing '{description}'.")
                 )
                 # Publish to broadcast so the agent (or router) picks it up
                 await self.redis.publish("broadcast", notification)
                 logger.info(f"OUTFIT: Updated state for {target_agent} and sent notification.")
             except Exception as e:
                 logger.error(f"OUTFIT: Failed to update state: {e}")

        try:
            asset_uri, asset_id = await self.visual.generate_and_index(
                agent_id=target_agent,
                prompt=description,
                tags=["outfit_change", "slash_command"],
                asset_type="pose",
                attitude="full_body"
            )
            
            # STORY 25.7: Auto-save to Vault
            if asset_id:
                # We already have the ID from generate_and_index
                await self.visual.vault.save_item(target_agent, description, asset_uri, description, category="garment", asset_id=asset_id)
                logger.info(f"VAULT_AUTO_SAVE: Successfully saved '{description}' for {target_agent}")
            else:
                logger.warning(f"VAULT_AUTO_SAVE: No asset_id returned for {asset_uri}")

        except Exception as e:
            await self._send_ack(msg, f"❌ Le changement de tenue pour {target_agent} a échoué: {e}")

    async def _run_location(self, args: list[str], msg: HLinkMessage):
        if not args:
            await self._send_ack(msg, "❌ Usage: /location [nom_agent] [lieu]")
            return

        target_agent = args[0]
        location_name = " ".join(args[1:]) if len(args) > 1 else ""
        
        known_agents = ["lisa", "renarde", "electra", "dieu"]
        if target_agent.lower() not in known_agents:
            location_name = " ".join(args)
            target_agent = "Renarde"

        await self._send_ack(msg, f"📍 {target_agent} se déplace vers : *{location_name}*...")
        
        # STORY 25.7: Check Vault
        vault_item = await self.visual.vault.get_item(target_agent, location_name, category="background")
        if vault_item:
            logger.info(f"VAULT_HIT: Found location '{location_name}' for {target_agent}")
            asset_uri = vault_item["asset"]["url"]
            if self.surreal:
                await self.surreal.update_agent_state(target_agent, "IS_IN", {"name": location_name, "description": location_name})
            
            await self.visual.notify_visual_asset(asset_uri, location_name, target_agent, "background")
            return

        if self.surreal:
             try:
                 target_data = {
                     "name": location_name,
                     "description": f"The {location_name}"
                 }
                 await self.surreal.update_agent_state(target_agent, "IS_IN", target_data)

                 notification = HLinkMessage(
                    type=MessageType.NARRATIVE_TEXT, 
                    sender=Sender(agent_id="system", role="orchestrator"),
                    recipient=Recipient(target=target_agent),
                    payload=Payload(content=f"[SYSTEM] Your state updated: You are now in '{location_name}'.")
                 )
                 await self.redis.publish("broadcast", notification)
                 logger.info(f"LOCATION: Updated state for {target_agent} and sent notification.")
             except Exception as e:
                 logger.error(f"LOCATION: Failed to update state: {e}")

        try:
            asset_uri, asset_id = await self.visual.generate_and_index(
                agent_id=target_agent,
                prompt=location_name,
                tags=["location_change", "slash_command"],
                asset_type="background"
            )

            # STORY 25.7: Auto-save to Vault
            logger.info(f"VAULT_AUTO_SAVE: Looking up location asset for {asset_uri}")
            query = f"SELECT id FROM visual_asset WHERE url = '{asset_uri}' LIMIT 1"
            res = await self.surreal._call("query", query)
            
            asset_id = None
            if isinstance(res, list) and len(res) > 0:
                first_stmt = res[0]
                results = first_stmt.get("result", []) if isinstance(first_stmt, dict) else first_stmt
                if results and len(results) > 0:
                    first_record = results[0]
                    asset_id = first_record.get("id")

            if asset_id:
                await self.visual.vault.save_item(target_agent, location_name, asset_uri, location_name, category="background", asset_id=asset_id)
                logger.info(f"VAULT_AUTO_SAVE: Successfully saved location '{location_name}' for {target_agent} -> ID: {asset_id}")
            else:
                logger.warning(f"VAULT_AUTO_SAVE: Could not find location record for URI {asset_uri} in DB. Result type: {type(res)}")

        except Exception as e:
            await self._send_ack(msg, f"❌ Le déplacement pour {target_agent} a échoué: {e}")

    async def _run_vault(self, args: list[str], msg: HLinkMessage):
        # 1. Try to get agent from args
        target_agent = args[0] if args else None
        
        # 2. Check if first arg is actually an agent name
        known_agents = ["lisa", "renarde", "electra", "dieu"]
        if target_agent and target_agent.lower() not in known_agents:
            target_agent = None

        # 3. Fallback to original recipient if it's a specific agent (Story 25.7)
        if not target_agent:
            if msg.recipient.target.lower() in known_agents:
                target_agent = msg.recipient.target
            else:
                target_agent = "Lisa" # Ultimate fallback

        items = await self.visual.vault.list_items(target_agent)
        if not items:
            await self._send_ack(msg, f"📦 Le vault de **{target_agent}** est vide.\n💡 Astuce: Demandez à {target_agent} d'enregistrer une tenue, ou utilisez `/vault [Nom]` pour voir un autre agent.")
            return

        lines = [f"📦 **Vault de {target_agent}** :"]
        for item in items:
            cat_icon = "👗" if item['category'] == "garment" else "📍"
            lines.append(f"{cat_icon} {item['category'].capitalize()}: **{item['name']}**")
        
        lines.append(f"\n💡 Pour réutiliser: `/outfit {target_agent} [Nom]` ou `/location {target_agent} [Nom]`")
        await self._send_ack(msg, "\n".join(lines))

    async def _send_ack(self, original_msg: HLinkMessage, text: str):
        ack = HLinkMessage(
            type=MessageType.NARRATIVE_TEXT,
            sender=Sender(agent_id="system", role="orchestrator"),
            recipient=Recipient(target="broadcast"),
            payload=Payload(content=text)
        )
        await self.redis.publish("broadcast", ack)