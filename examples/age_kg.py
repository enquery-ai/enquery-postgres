import psycopg2
from psycopg2 import sql

# Database connection parameters
DB_PARAMS = {
    "dbname": "enqueldb",
    "user": "enqueluser",
    "password": "enquelpass",
    "host": "localhost",
    "port": "5432"
}

def execute_query(connection, query):
    """Execute a single query."""
    with connection.cursor() as cursor:
        cursor.execute(query)
        connection.commit()

def graph_exists(connection, graph_name):
    """Check if the graph already exists."""
    query = sql.SQL("SELECT * FROM ag_catalog.ag_graph WHERE name = %s")
    with connection.cursor() as cursor:
        cursor.execute(query, (graph_name,))
        return cursor.fetchone() is not None

def main():
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(**DB_PARAMS)

        graph_name = 'my_knowledge_graph'

        # Check if the graph exists
        if not graph_exists(conn, graph_name):
            print(f"Graph '{graph_name}' does not exist. Creating the graph.")
            
            # Enable AGE extension and create the graph
            execute_query(conn, "CREATE EXTENSION IF NOT EXISTS age;")
            execute_query(conn, "SET search_path = ag_catalog, '$user', public;")
            execute_query(conn, f"SELECT create_graph('{graph_name}');")

            # Create vertices
            create_vertices = """
            SELECT * FROM cypher('my_knowledge_graph', $$ 
                CREATE (a:Person {name: 'Alice', age: 30}), 
                       (b:Person {name: 'Bob', age: 25}),
                       (c:Person {name: 'Carol', age: 35})
            $$) as (a agtype);
            """
            execute_query(conn, create_vertices)

            # Create edges
            create_edges = [
                """
                SELECT * FROM cypher('my_knowledge_graph', $$
                    MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) 
                    CREATE (a)-[:FRIEND]->(b)
                $$) as (a agtype);
                """,
                """
                SELECT * FROM cypher('my_knowledge_graph', $$
                    MATCH (a:Person {name: 'Alice'}), (c:Person {name: 'Carol'}) 
                    CREATE (a)-[:FRIEND]->(c)
                $$) as (a agtype);
                """,
                """
                SELECT * FROM cypher('my_knowledge_graph', $$
                    MATCH (b:Person {name: 'Bob'}), (c:Person {name: 'Carol'}) 
                    CREATE (b)-[:FRIEND]->(c)
                $$) as (a agtype);
                """
            ]
            for query in create_edges:
                execute_query(conn, query)

        else:
            print(f"Graph '{graph_name}' already exists.")

        # Function to execute cypher queries
        def execute_cypher(connection, query):
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM cypher('{graph_name}', $$ {query} $$) as (result agtype);")
                results = cursor.fetchall()
                for result in results:
                    print(result[0])

        # Query: Get all persons
        print("All Persons:")
        execute_cypher(conn, "MATCH (n:Person) RETURN n")

        # Query: Get friends of Alice
        print("\nFriends of Alice:")
        execute_cypher(conn, "MATCH (a:Person {name: 'Alice'})-[:FRIEND]->(friends) RETURN friends")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
