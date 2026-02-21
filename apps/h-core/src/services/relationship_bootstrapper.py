import logging
from typing import Any, Dict, List
from src.infrastructure.surrealdb import SurrealDbClient

logger = logging.getLogger(__name__)


class RelationshipBootstrapper:
    def __init__(self, surreal: SurrealDbClient):
        self.surreal = surreal

    async def bootstrap_relationships(self, agents: List[Dict[str, Any]]):
        """Bootstrap initial KNOWS and TRUSTS edges between agents."""
        logger.info("BOOTSTRAP: Starting relationship bootstrapping...")

        created_edges = {"KNOWS": 0, "TRUSTS": 0}
        for i, agent1 in enumerate(agents):
            for j, agent2 in enumerate(agents):
                if i == j:
                    continue  # Skip self-relationships

                # Standardize IDs (must match how subjects are created elsewhere)
                a1_id = agent1["name"].lower().replace(" ", "_")
                a2_id = agent2["name"].lower().replace(" ", "_")

                # Ensure subjects exist (safety)
                await self.surreal._call(
                    "query",
                    f"INSERT INTO subject (id, name) VALUES (subject:`{a1_id}`, $name) ON DUPLICATE KEY UPDATE name=$name;",
                    {"name": agent1["name"]},
                )

                # Check existence helper
                async def edge_exists(edge_table):
                    # SurrealDB: 'in' is source, 'out' is target
                    query = f"SELECT * FROM {edge_table} WHERE in = subject:`{a1_id}` AND out = subject:`{a2_id}`;"
                    res = await self.surreal._call("query", query)
                    return res and isinstance(res, list) and len(res) > 0 and res[0].get("result")

                # Create KNOWS edge if not exists
                if not await edge_exists("KNOWS"):
                    await self.surreal._call(
                        "query",
                        f"RELATE subject:`{a1_id}`->KNOWS->subject:`{a2_id}` SET strength = 1.0, timestamp = time::now();",
                    )
                    created_edges["KNOWS"] += 1

                # Create TRUSTS edge with logic-based level
                if not await edge_exists("TRUSTS"):
                    trust_level = 0.5  # Default
                    if agent1.get("role") == agent2.get("role"):
                        trust_level = 0.8
                    elif agent1.get("name") == "Renarde" or agent2.get("name") == "Renarde":
                        trust_level = 0.9  # Coordinator trust

                    await self.surreal._call(
                        "query",
                        f"RELATE subject:`{a1_id}`->TRUSTS->subject:`{a2_id}` SET level = {trust_level}, timestamp = time::now();",
                    )
                    created_edges["TRUSTS"] += 1

        logger.info(f"BOOTSTRAP: Created {created_edges['KNOWS']} KNOWS and {created_edges['TRUSTS']} TRUSTS edges.")
        return created_edges
