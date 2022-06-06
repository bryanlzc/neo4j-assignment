#!/usr/bin/env python
# coding: utf-8

# In[112]:


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
neo4jUri = r"neo4j://< ip_addr >"
userName = "neo4j"
password = "test"

conn = Neo4jConnection(neo4jUri, userName, password)

# Creating a new Database testdb for ingestion
conn.query("CREATE OR REPLACE DATABASE testdb")


# In[116]:


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

# Ingesting trips dataset to testdb using the data model
conn.query(query_string, db='testdb')


# In[117]:


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

# Ingesting education dataset to testdb using the data model
conn.query(query_string, db='testdb')


# In[118]:


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

# Ingesting work dataset to testdb using the data model
conn.query(query_string, db='testdb')


# In[119]:


# Data model for transaction dataset
query_string = '''

    LOAD CSV WITH HEADERS FROM 'https://gist.githubusercontent.com/maruthiprithivi/10b456c74ba99a35a52caaffafb9d3dc/raw/a46af9c6c4bf875ded877140c112e9ff36f8f2e8/sng_transaction.csv' as row
    MATCH (p:person { name: row.name, passportnumber: row.passportnumber })      
    MERGE (m:merchant {name: row.merchant, country: row.country })
    MERGE (co:country {country: row.country})
    MERGE (p)-[:makes_transaction_at {transactiondate: row.transactiondate, amount: row.amount, cardnumber: row.cardnumber}]->(m)
    MERGE (p)-[:makes_transaction_in]->(co)
    
'''

# Ingesting transaction dataset to testdb using the data model
conn.query(query_string, db='testdb')


# In[120]:


# Creating person_name index
query_string = '''

    CREATE INDEX person_name FOR (p:person) ON (p.name)

'''

conn.query(query_string, db='testdb')


# In[121]:


# Creating country_name index
query_string = '''

    CREATE INDEX country_name FOR (co:country) ON (co.country)

'''

conn.query(query_string, db='testdb')

    


# In[122]:


# Creating institution_name index
query_string = '''

    CREATE INDEX institution_name FOR (i:institution) ON (i.name)

'''

conn.query(query_string, db='testdb')


# In[115]:


query_string = '''
    MATCH (n)
    DETACH DELETE n
'''

conn.query(query_string, db='testdb')


# In[ ]:




