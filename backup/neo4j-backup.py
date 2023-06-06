import os
import datetime
import zipfile
import sys
import yaml
from azure.storage.blob import BlobServiceClient

URL_BACKUP = 'urlbackup'
DB_BACKUP = 'dbbackup'
STORAGE_NAME = 'storagename'
TOKEN_CRED = 'tokencredential'
CONTAINER_NAME = 'containername'
URL_GCP_CREDENTIALS = 'pathcreadentialsgcp'
NAME_DIRECTORY = 'neo4j_backup'
NAME_FILE_ZIP = 'neo4j_backup.zip'
FROM_SERVER = '4.236.162.225:6362'
BACKUP_CMD = 'sudo /home/neo4j-enterprise-4.4.19/bin/neo4j-admin backup --backup-dir={} --database={}'
FORMAT_DATE = '%m-%d-%Y_%H-%M-%S'
MESSAGE_UPLOAD_FILE = 'File {} uploaded to {}.'




def validate_environment_variables(args):
    try:
        with open(args[1]) as file:
            config_list = yaml.load(file, Loader=yaml.FullLoader)

            global url_backup
            url_backup = config_list[URL_BACKUP]

            if(not url_backup):
                print('The config variable urlbackup doesnt exist')
                return False

            global db_backup
            db_backup = config_list[DB_BACKUP]

            if(not db_backup):
                print('The config variable dbbackup doesnt exist')
                return False

            global container_name
            container_name = config_list[CONTAINER_NAME]

            if(not container_name):
                print('The config variable containername doesnt exist')
                return False

            global storage_name
            storage_name = config_list[STORAGE_NAME]

            if(not container_name):
                print('The config variable storagename doesnt exist')
                return False


            global token_credential
            token_credential = config_list[TOKEN_CRED]

            if(not container_name):
                print('The config variable tokencredential doesnt exist')
                return False

    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    global url_backup_file_zip
    url_backup_file_zip = url_backup + NAME_FILE_ZIP
    
    return True


def execute_command_backup():
    backup_cmd_tmp = BACKUP_CMD.format(url_backup,db_backup)
    # Execute backup command
    return os.popen(backup_cmd_tmp).read()



def upload_data_to_blob(data_bytes, file_name):
    blob_service_client = BlobServiceClient(
        account_url="https://"+storage_name +".blob.core.windows.net",
        credential=token_credential
    )
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)
    blob_client.upload_blob(data_bytes)
    return "updated"




def upload_backup_file(path_file_upload):

    date = datetime.datetime.today().strftime(FORMAT_DATE)
    name_file_tpm = os.path.basename(path_file_upload)
    uri_upload = date + "/" + name_file_tpm

    with open(path_file_upload, 'rb') as f:
        data = f.read()
    f.close()

    upload_data_to_blob(data, uri_upload)

    print(
        MESSAGE_UPLOAD_FILE.format(
            name_file_tpm, uri_upload
        )
    )



def zip_directory(path):
   with zipfile.ZipFile(url_backup_file_zip, 'w', zipfile.ZIP_DEFLATED) as file_write:
       for root, dirs, files in os.walk(path):
           for file in files:
               file_write.write(os.path.join(root, file))


def remove_zip_file():
   os.remove(url_backup_file_zip)


def create_backup():
    if(len(sys.argv) < 2):
        print('The arguments are invalid')
        return

    if(validate_environment_variables(sys.argv)):
        execute_command_backup()
        # zip_directory(url_backup)
        # upload_backup_file(url_backup_file_zip)
        # remove_zip_file()


create_backup()
