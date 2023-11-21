import os
from azure.storage.blob import BlobServiceClient # pip install azure-storage-blob
from azure.core.exceptions import ResourceExistsError

storage_connection_string = 'DefaultEndpointsProtocol=https;AccountName=iotnhom12;AccountKey=i9TSMSjG1HbCj2Uz+3bbFeiMis2kSrS6P5Dm1le9C3mn99L4vTcFM6tHNzmnWL/B2Udk9Ggr/zvs+AStvTZO/w==;EndpointSuffix=core.windows.net'
blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)

container_id = 'picture'
blob_service_client.get_container_client(container_id)

overwrite = False
target_directory = os.path.join(os.getcwd(), 'picture')

for folder in os.walk(target_directory):
    for file in folder[-1]:
        try:
            blob_path = os.path.join(folder[0].replace(os.getcwd() + '\\', ''), file)
            blob_obj = blob_service_client.get_blob_client(container=container_id, blob=blob_path)
            
            with open(os.path.join(folder[0], file), mode='rb') as file_data:
                blob_obj.upload_blob(file_data, overwrite=overwrite)
        except ResourceExistsError:
            print('Blob "{0}" already exists'.format(blob_path))
            print()
            continue