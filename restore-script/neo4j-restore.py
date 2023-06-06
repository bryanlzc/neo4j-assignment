import yaml
import os
import sys
from neo4j import GraphDatabase



URL_RESTORE = 'urlrestore'
DB_RESTORE = 'dbrestore'
BACKUP_CMD = 'sudo /home/neo4j-enterprise-4.4.19/bin/neo4j-admin restore --from={} --database={}'
USERNAME = 'username'
PASSWORD = 'password'
SCHEME = 'scheme'
HOST = 'host'
PORT = 'port'


def validate_environment_variables(args):
    try:
        with open(args[1]) as file:
            config_list = yaml.load(file, Loader=yaml.FullLoader)

            global url_restore
            url_restore = config_list[URL_RESTORE]

            if(not url_restore):
                print('The config variable urlrestore doesnt exist')
                return False


            global db_restore
            db_restore = config_list[DB_RESTORE]
            if(not db_restore):
                print('The config variable dbrestore doesnt exist')
                return False

            global username
            username = config_list[USERNAME]
            if(not username):
                print('The config variable username doesnt exist')
                return False
            
            global password
            password = config_list[PASSWORD]
            if(not password):
                print('The config variable password doesnt exist')
                return False

            global driver_url
            scheme = config_list[SCHEME]
            if(not scheme):
                print('The config variable scheme doesnt exist')
                return False
            host = config_list[HOST]
            if(not host):
                print('The config variable host doesnt exist')
                return False
            port = config_list[PORT]
            if(not port):
                print('The config variable port doesnt exist')
                return False
            driver_url = f'{scheme}://{host}:{port}'


    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    global url_restore_dir
    url_restore_dir = url_restore + db_restore
    return True

def execute_command_restore():
    restore_cmd_tmp = BACKUP_CMD.format(url_restore_dir, db_restore)
    print(restore_cmd_tmp)
    # Execute backup command
    return os.popen(restore_cmd_tmp).read()



def create_database(tx, dbname):
    return tx.run( "create database $dbname", dbname= dbname)


def execute_cypher_create_db():
    driver = GraphDatabase.driver(driver_url, auth=(username, password))
    try:
        driver.verify_connectivity()
    except Exception as e:
        return e
    
    with driver.session(database= "system") as session:
        session.write_transaction(create_database, dbname=db_restore)
    

def restore():
    if(len(sys.argv) < 2):
        print('The arguments are invalid')
        return

    if(validate_environment_variables(sys.argv)):
        execute_command_restore()
        execute_cypher_create_db()
        print('done')



# run restore function
restore()
