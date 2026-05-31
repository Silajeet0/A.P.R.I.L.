from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password123"

AUTH = (USERNAME, PASSWORD)

class MemoryEngine:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=AUTH)
        self._initialize_constraints()

    def close(self):
        self.driver.close()
    
    def ensure_label_constraint(self, label_name):
        """Dynamically registers a uniqueness constraint if a new label is discovered."""
        sanitized_label = label_name.strip().capitalize()
        constraint_query = f"""
        CREATE CONSTRAINT unique_{sanitized_label.lower()}_name IF NOT EXISTS 
        FOR (n:{sanitized_label}) REQUIRE n.name IS UNIQUE
        """
        with self.driver.session() as session:
            try:
                session.run(constraint_query)
            except Exception:
                pass 

    def _initialize_constraints(self):
        '''Ensures Neo4j enforces unique entity names to avoid duplicate bubbles'''

        queries = [
            "CREATE CONSTRAINT unique_user_name IF NOT EXISTS FOR (u:User) REQUIRE u.name IS UNIQUE",
            "CREATE CONSTRAINT unique_project_name IF NOT EXISTS FOR (p:Project) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT unique_entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE"
        ]

        with self.driver.session() as session:
            for q in queries:
                try:
                    session.run(q)
                except Exception as e:
                    pass

    def commit_relationship(self, source_node:str, source_label:str, relationship:str, target_node:str, target_label:str)->str:
        '''Executes an atomic MERGE operation to dynamically grow the graph canvas'''

        s_label = source_label.strip().capitalize()
        t_label = target_label.strip().capitalize()
        rel_type = relationship.strip().replace(" ", "_").upper()

        self.ensure_label_constraint(s_label)
        self.ensure_label_constraint(t_label)

        query = f"""
        MERGE (s:{s_label} {{name: $s_name}})
        MERGE (t:{t_label} {{name: $t_name}})
        MERGE (s)-[r:{rel_type}]->(t)
        RETURN type(r)
        """

        try:
            with self.driver.session() as session:
                session.run(query, s_name=source_node, t_name=target_node)
            return f"Successfully saved connection: ({source_node})-[:{rel_type}]->({target_node})"
        except Exception as e:
            return f"Database mutation failed: {str(e)}"
        
    def get_user_context(self, user:str="Silajeet")->str:
        """fetches the knowledge about the user"""
        query = """MATCH (u:User {name: $name})-[r]->(target)
                RETURN type(r) AS relationship, target.name AS value, labels(target)[0] AS category"""
        try:
            with self.driver.session() as session:
                result = session.run(query, name=user)
                facts = []
                for record in result:
                    rel = record["relationship"]
                    val = record["value"]
                    cat = record["category"]

                    facts.append(f"-User {user} has relationship {rel} with {cat} '{val}'.")
            if len(facts) > 0:
                return "\n".join(facts)
            else:
                return "No prior long-term memory profiles found for this user."
        except Exception as e:
            return f"No information about user: {user} in data. Exception Raised: {e}"
        
# Instantiate a singleton instance for the brain to use
memory_db = MemoryEngine()