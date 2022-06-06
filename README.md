# neo4j-assignment

## Setting up Neo4j Enterprise on Docker
Pre-requisite: Linux distributed OS, Docker, Python, Jupyter Notebook, Internet connection

Run the command below to pull Neo4j Enterprise image to Local docker repository (latest = 4.4.7)
```
$ docker pull neo4j:enterprise
```
Run the command below to run Neo4j Enterprise as a docker container
```
$ docker run --name neo4jEnterprise --publish=7474:7474 --publish=7687:7687 --volume=$HOME/neo4j/data:/data --volume=$HOME/neo4j/logs:/logs --volume=$HOME/neo4j/import:/var/lib/neo4j/import --volume=$HOME/neo4j/plugins:/plugins --env NEO4J_AUTH=neo4j/test --env NEO4J_ACCEPT_LICENSE_AGREEMENT=yes -d neo4j:enterprise 
```
## Note: 
**Ports**

Port 7474 and Port 7687 is binded for HTTP and Bolt access to Neo4j API respectively 

**Env parameters**

*NEO4J_AUTH* - Allow parsing of username and password parameters

*NEO4J_ACCEPT_LICENSE_AGREEMENT* - Neo4j license agreement

**Volume mounts**

*data* - Map local directory for Data storage

*logs* - Map local directory for Logs storage

## Access Neo4j Web Browser

To access Neo4j web browser, access the below URL via web browser
```
http://< ip_addr >:7474
```

To Login
```
username: neo4j
password: test
```

# Ingest Data to Neo4j

Pre-requisite: Install Neo4j python library
```
pip3 install neo4j
```
## Using Social Network dataset [Social Network](https://gist.github.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc)

## Connection class to connect to Neo4j server
Run the below in Jupyter Notebook to establish connection to Neo4j server:
```
from neo4j import GraphDatabase

class Neo4jConnection:
    
    def __init__(self, neo4jUri, userName, password):
        self.__uri = neo4jUri
        self.__user = userName
        self.__pwd = password
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
        except Exception as e:
            print("Failed to create the driver:", e)
        
    def close(self):
        if self.__driver is not None:
            self.__driver.close()
        
    def query(self, query, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try: 
            session = self.__driver.session(database=db) if db is not None else self.__driver.session() 
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally: 
            if session is not None:
                session.close()
        return response

# Neo4j Server Credentials
neo4jUri = r"neo4j://< ip_addr >:7687"
userName = "neo4j"
password = "test"

conn = Neo4jConnection(neo4jUri, userName, password)

# Creating a new Database testdb for ingestion
conn.query("CREATE OR REPLACE DATABASE testdb")
```

## Ingesting trips dataset [trips.csv](https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_trips.csv)
```
# Data model for trips dataset
query_string = '''

    LOAD CSV WITH HEADERS FROM 'https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_trips.csv' as row
    MERGE (p:person {name: row.name, passportnumber: row.passportnumber, citizenship: row.citizenship})
    WITH p
    LOAD CSV WITH HEADERS FROM 'https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_trips.csv' as row
    MATCH (p:person {name: row.name, passportnumber: row.passportnumber, citizenship: row.citizenship})
    MERGE (o:origin { country: row.departurecountry})
    MERGE (p)-[:is_departing_from]->(o)
    WITH p,o
    LOAD CSV WITH HEADERS FROM 'https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_trips.csv' as row
    MATCH (o:origin { country: row.departurecountry})
    MERGE (dd:departuredate {date: row.departuredate})
    MERGE (o)-[:on]->(dd)
    WITH o,dd,p
    LOAD CSV WITH HEADERS FROM 'https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_trips.csv' as row
    MATCH (dd:departuredate {date: row.departuredate})
    MERGE (dc:destination { country: row.arrivalcountry})
    MERGE (c:country { country: row.arrivalcountry})
    MERGE (ad:arrivaldate { date: row.arrivaldate})
    MERGE (dd)-[:to]->(dc)-[:arriving_on]->(ad)
    MERGE (p)-[:travelling_to]->(c)

'''

# Ingesting trips dataset to neo4j using the data model
conn.query(query_string, db='neo4j')
```
Note: 

As there are multiple identical person in the trips dataset, we first use the MERGE clause to ensure that duplicated nodes with label:person and having the same properties will not be created.

Thereafter, upon MATCH condition, MERGE the other nodes with the following labels (departuredate, origin, destination, arrivaldate) as specified above and create the relationship

## Ingesting education dataset [education.csv](https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_education.csv)

```
# Data model for education dataset
query_string = '''

    LOAD CSV WITH HEADERS FROM 'https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_education.csv' as row
    MATCH (p:person { name: row.name, passportnumber: row.passportnumber })
    MERGE (i:institution {name: row.nameofinstitution, country: row.country })
    MERGE (c:course {name: row.course })
    ON CREATE SET p.name = row.name, p.passportnumber = row.passportnumber
    MERGE (c)<-[:enrolled_in {startyear: row.startyear, endyear: row.endyear}]-(p)-[:studied_in {startyear: row.startyear, endyear: row.endyear}]->(i)
    WITH i,c,p
    LOAD CSV WITH HEADERS FROM 'https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_education.csv' as row
    MATCH (i:institution {name: row.nameofinstitution, country: row.country })
    MERGE (i)-[:offers]->(c)
    WITH i,p
    LOAD CSV WITH HEADERS FROM 'https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_education.csv' as row
    MATCH (i:institution {name: row.nameofinstitution, country: row.country })
    MERGE (co:country {country: row.country})
    MERGE (i)-[:located_in]->(co)
    MERGE (p)-[:studied_in]->(co)
'''


# Ingesting education dataset to neo4j using the data model
conn.query(query_string, db='neo4j')

```

## Ingesting work dataset [work.csv](https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_work.csv)
```
# Data model for work dataset
query_string = '''

    LOAD CSV WITH HEADERS FROM 'https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_work.csv' as row
    MATCH (p:person { name: row.name, passportnumber: row.passportnumber })      
    MERGE (o:organization {name: row.nameoforganization, country: row.country })
    MERGE (des:designation { name: row.designation})
    MERGE (des)<-[:designation_is {startyear: row.startyear, endyear: row.endyear}]-(p)-[:works_for {startyear: row.startyear, endyear: row.endyear}]->(o)
    WITH o,p,des
    LOAD CSV WITH HEADERS FROM 'https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_work.csv' as row
    MATCH (o:organization {name: row.nameoforganization, country: row.country })
    MERGE (o)-[:holding_designation_of]->(des)
    
'''

# Ingesting work dataset to neo4j using the data model
conn.query(query_string, db='neo4j')

```

## Ingesting transaction dataset [transaction.csv](https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_transaction.csv)

```
# Data model for transaction dataset
query_string = '''

    LOAD CSV WITH HEADERS FROM 'https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_transaction.csv' as row
    MATCH (p:person { name: row.name, passportnumber: row.passportnumber })      
    MERGE (m:merchant {name: row.merchant, country: row.country })
    MERGE (co:country {country: row.country})
    MERGE (p)-[:makes_transaction_at {transactiondate: row.transactiondate, amount: row.amount, cardnumber: row.cardnumber}]->(m)
    MERGE (p)-[:makes_transaction_in]->(co)
    
'''

# Ingesting transaction dataset to neo4j using the data model
conn.query(query_string, db='testdb')

```

# Creating Index 

## Purpose: Optimize query performance for node properties used in frequent lookups
```
# Creating person_name index
query_string = '''

    CREATE INDEX person_name FOR (p:person) ON (p.name)

'''

conn.query(query_string, db='testdb')
```

```
# Creating country_name index
query_string = '''

    CREATE INDEX country_name FOR (co:country) ON (co.country)

'''

conn.query(query_string, db='testdb')
```

```
# Creating institution_name index
query_string = '''

    CREATE INDEX institution_name FOR (i:institution) ON (i.name)

'''

conn.query(query_string, db='testdb')
```

# Cypher queries 
## Finding the total transacted amount in each individual country sorted by descending order (Answer: Vietnam - Highest amount transacted)

```
MATCH (p:person)-[t:makes_transaction_at]->(m:merchant)
RETURN m.country AS country, sum(toInteger(substring(t.amount, 1))) AS country_total_transaction
ORDER BY country_total_transaction DESC

```

Note: t.amount has Datatype string due to "$" and could be taken care of during the ingestion using the substring method or during query as shown above

## Finding frequency of travel per year 
```
MATCH (p:person)-[d:is_departing_from]->(ori:origin)-[o:on]->(dep:departuredate)-[t:to]->(arr:destination)
RETURN p.name as name, toInteger(right(dep.date,4)) as year, count(toInteger(right(dep.date,4))) as freq_travel
ORDER BY year
```

## Top 5 most popular destination (Answer: Vietnam - Most popular destination)
```
MATCH (p:person)-[d:is_departing_from]->(ori:origin)-[o:on]->(dep:departuredate)-[t:to]->(arr:destination)
RETURN arr.country as country, count(arr.country) as freq
ORDER BY freq DESC
LIMIT 5
```

## Use case: Finding persons with similar travel history to Vietnam by date
```
MATCH (p:person)-[d:is_departing_from]->(ori:origin)-[o:on]->(dep:departuredate)-[t:to]->(arr:destination {country:'Vietnam'})-[aon:arriving_on]->(ad:arrivaldate)
RETURN collect(p.name) as list_of_person_arriving_in_vietnam, ad.date as date
```

## Use case: Finding relationship connected by Vietnam between the 3 person
```
MATCH (p:person)-[relationship]->(c:country { country: "Vietnam"})
RETURN p,relationship,c
```

# Ingest Data to Neo4j Sandbox Environment for Neo4j Bloom analysis
## Provision a Neo4j Sandbox Environment 

Register for an account with a valid email address

Create a blank sandbox environment


## Connecting to Neo4j Sandbox Environment
```
from neo4j import GraphDatabase

class Neo4jConnection:
    
    def __init__(self, neo4jUri, userName, password):
        self.__uri = neo4jUri
        self.__user = userName
        self.__pwd = password
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__user, self.__pwd))
        except Exception as e:
            print("Failed to create the driver:", e)
        
    def close(self):
        if self.__driver is not None:
            self.__driver.close()
        
    def query(self, query, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try: 
            session = self.__driver.session(database=db) if db is not None else self.__driver.session() 
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally: 
            if session is not None:
                session.close()
        return response

# Database Credentials
neo4jUri = r"bolt://18.234.160.74:7687"
userName = "neo4j"
password = "regulation-quarterdecks-centerlines"

conn = Neo4jConnection(neo4jUri, userName, password)

```

## Note: Re-use queries above and replace conn.query(query_string, db='testdb') to conn.query(query_string, db='neo4j')

# BLOOM

## Generate new perspective with Bloom
![image](https://user-images.githubusercontent.com/19281954/172133559-65cd5492-c8a6-4421-bfee-f301b038c4f7.png)

## Starting with Person nodes
<img width="960" alt="Bloom - Person (Relationship)" src="https://user-images.githubusercontent.com/19281954/172133353-11b2df10-3048-49ca-b6c5-b19313dcc290.png">

Hold shift and click on the Person nodes

Right click and expand relationship for studied_in, travelling_to, makes_transaction_in

Expanding relationship to obtain the graph as shown above

## Using search bar to search for relationships
<img width="960" alt="Bloom - Person (Relationship 2)" src="https://user-images.githubusercontent.com/19281954/172134008-9cf8b358-bb28-4f5f-938d-b1ff69707b49.png">


# INSIGHTS

Alice Gan, Ariff Johan and Anil Kumar are friends/acquaintance from Smart National University of Vietnam and travelled again to Vietnam on the same date together living in the same hotel (Grand Coconut Hotel, Vietnam)








