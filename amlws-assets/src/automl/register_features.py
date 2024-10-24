# register_features.py
import argparse
from pathlib import Path
import pandas as pd
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Data
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential
import mlflow
import logging
import time
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser("register_features")
    parser.add_argument("--features_input", type=str, help="Path to features parquet file")
    parser.add_argument("--data_name", type=str, help="Name for registered data asset")
    parser.add_argument("--description", type=str, default="EEG features for depression classification")
    parser.add_argument("--registered_features_output", type=str, help="Path to output registered features")
    parser.add_argument("--ml_client_json", type=str, help="JSON string of MLClient configuration")
    args = parser.parse_args()
    return args

def main():
    mlflow.start_run()
    args = parse_args()
    
    try:
        start_time = time.time()
        
        # Initialize MLClient
        ml_client_config = json.loads(args.ml_client_json)
        credential = DefaultAzureCredential()
        ml_client = MLClient(
            credential=credential,
            subscription_id=ml_client_config['subscription_id'],
            resource_group_name=ml_client_config['resource_group'],
            workspace_name=ml_client_config['workspace_name']
        )
        
        logger.info(f"Registering features from: {args.features_input}")
        
        # Create MLTable definition
        mltable_data = Data(
            path=args.features_input,
            type=AssetTypes.MLTABLE,
            description=args.description,
            name=args.data_name,
            version='1.0.0'
        )
        
        # Register the data
        registered_data = ml_client.data.create_or_update(mltable_data)
        
        # Log registration metrics
        mlflow.log_metric("registration_time", time.time() - start_time)
        mlflow.log_metric("registration_status", 1)
        
        logger.info(f"Features registered as MLTable: {registered_data.name}, version: {registered_data.version}")
        
        # Save the registered features path
        with open(args.registered_features_output, "w") as f:
            f.write(registered_data.path)
        logger.info(f"Registered features path saved to: {args.registered_features_output}")
        
    except Exception as e:
        logger.error(f"Error registering features: {str(e)}")
        mlflow.log_metric("registration_status", 0)
        raise
    finally:
        mlflow.end_run()

if __name__ == "__main__":
    main()