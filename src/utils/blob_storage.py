import logging
import os
import re

import gradio as gr
from azure.storage.blob import BlobServiceClient


def download_idx_from_storage(
    state, storage_connection_str, storage_container_name
):
    """
    Downloads index files from Azure Blob Storage to a local directory.

    This function connects to an Azure Blob Storage container, lists the blobs
    within a specified prefix, filters for date-formatted folder names, and
    downloads the contents of those folders to a local directory called
    'graphdata'. It creates the necessary local folder structure if it
    does not already exist.

    Args:
        state: The current state of the application, used for tracking and
                updating context.
        storage_connection_str (str): The connection string for the Azure Blob
                                        Storage account.
        storage_container_name (str): The name of the container from which to
                                        download the blobs.

    Returns:
        The updated state after the download process is complete.

    Raises:
        Exception: If any error occurs during the download process,
                    the function will raise an exception.
    """
    blob_service_client = BlobServiceClient.from_connection_string(
        storage_connection_str
    )
    container_client = blob_service_client.get_container_client(
        storage_container_name
    )
    # list outputs/ folder
    blob_list = container_client.list_blobs(name_starts_with="output/")
    date_folders = set()
    for blob in blob_list:
        # get outputs/ folder names
        folder_path = os.path.dirname(blob.name)
        logging.info(f"folderPath: {folder_path}")
        folder_name = folder_path.split("/")[1]
        gr.Info(f"got folderName: {folder_name}", duration=5)
        if is_date_format_folder(folder_name):
            date_folders.add(folder_path)

    # if theres not downloaded folder, create new folder
    if not os.path.exists("./graphdata"):
        os.makedirs("./graphdata")

    for folder in date_folders:
        gr.Info(f"Downloading folder: {folder}", duration=5)
        blobs_in_folder = container_client.list_blobs(name_starts_with=folder)

        for blob in blobs_in_folder:
            local_path = os.path.join("./graphdata", blob.name)
            local_folder = os.path.dirname(local_path)
            if not os.path.exists(local_folder):
                os.makedirs(local_folder)

            with open(local_path, "wb") as download_file:
                download_stream = container_client.download_blob(blob.name)
                download_file.write(download_stream.readall())

        gr.Info(f"Downloaded RAGindexes to {folder}", duration=5)
    gr.Info(f"All successfully downloaded index from storage!", duration=10)

    return state


def is_date_format_folder(folder_name):
    """Function to search date format folder"""
    pattern = r"\d{8}-\d{6}"  # e.g.) 20240909-182823
    return re.match(pattern, folder_name) is not None
