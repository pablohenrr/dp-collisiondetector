import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

STORAGE_ACCOUNT_NAME = os.getenv("STORAGE_ACCOUNT_NAME")
STORAGE_ACCOUNT_KEY = os.getenv("STORAGE_ACCOUNT_KEY")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")

BLOB_URL = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/"

LOCAL_DIRECTORY = "accident-detector-dataset"

def upload_files_to_blob(storage_account_name: str, storage_account_key: str, container_name: str, blob_url: str, local_directory: str):

    blob_service_client = BlobServiceClient(account_url=blob_url, credential=storage_account_key)
    container_client = blob_service_client.get_container_client(container_name)

    if not container_client.exists():
        container_client.create_container()

    for root, dirs, files in os.walk(local_directory):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            blob_name = os.path.relpath(file_path, local_directory)
            print(f"Uploading {file_path} as {blob_name}...")
            blob_client = container_client.get_blob_client(blob_name)
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            print(f"Uploaded {file_name} to container '{container_name}'.")

if __name__ == "__main__":
    upload_files_to_blob(STORAGE_ACCOUNT_NAME, STORAGE_ACCOUNT_KEY, CONTAINER_NAME, BLOB_URL, LOCAL_DIRECTORY)