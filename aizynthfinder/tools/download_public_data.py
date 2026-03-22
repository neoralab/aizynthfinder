"""Module with script to download public data."""
import argparse
import os
import posixpath
import sys
from urllib.parse import urlparse

import requests
import tqdm

FILES_TO_DOWNLOAD = {
    "policy_model_onnx": {
        "filename": "uspto_model.onnx",
        "url": "https://zenodo.org/record/7797465/files/uspto_model.onnx",
    },
    "template_file": {
        "filename": "uspto_templates.csv.gz",
        "url": "https://zenodo.org/record/7341155/files/uspto_unique_templates.csv.gz",
    },
    "ringbreaker_model_onnx": {
        "filename": "uspto_ringbreaker_model.onnx",
        "url": "https://zenodo.org/record/7797465/files/uspto_ringbreaker_model.onnx",
    },
    "ringbreaker_templates": {
        "filename": "uspto_ringbreaker_templates.csv.gz",
        "url": "https://zenodo.org/record/7341155/files/uspto_ringbreaker_unique_templates.csv.gz",
    },
    "stock": {
        "filename": "zinc_stock.hdf5",
        "url": "https://ndownloader.figshare.com/files/23086469",
    },
    "filter_policy_onnx": {
        "filename": "uspto_filter_model.onnx",
        "url": "https://zenodo.org/record/7797465/files/uspto_filter_model.onnx",
    },
}

YAML_TEMPLATE = """expansion:
  uspto:
    - {}
    - {}
  ringbreaker:
    - {}
    - {}
filter:
  uspto: {}
stock:
  zinc: {}
"""


def _join_data_path(base_path: str, filename: str) -> str:
    if base_path.startswith("gs://"):
        parsed = urlparse(base_path)
        remote_path = posixpath.join(parsed.netloc, parsed.path.lstrip("/"), filename)
        return f"gs://{remote_path}"
    return os.path.join(os.path.abspath(base_path), filename)


def _download_file(url: str, filename: str) -> None:
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        pbar = tqdm.tqdm(
            total=total_size, desc=os.path.basename(filename), unit="B", unit_scale=True
        )
        with open(filename, "wb") as fileobj:
            for chunk in response.iter_content(chunk_size=1024):
                fileobj.write(chunk)
                pbar.update(len(chunk))
        pbar.close()


def main() -> None:
    """Entry-point for CLI"""
    parser = argparse.ArgumentParser("download_public_data")
    parser.add_argument(
        "path",
        default=".",
        help="the local path to download the files and write config.yml",
    )
    parser.add_argument(
        "--gcs-path",
        help="optional gs:// path to use in config.yml instead of local file paths",
    )
    args = parser.parse_args()
    path = args.path

    try:
        for filespec in FILES_TO_DOWNLOAD.values():
            _download_file(filespec["url"], os.path.join(path, filespec["filename"]))
    except requests.HTTPError as err:
        print(f"Download failed with message {str(err)}")
        sys.exit(1)

    config_base_path = args.gcs_path or path
    with open(os.path.join(path, "config.yml"), "w") as fileobj:
        fileobj.write(
            YAML_TEMPLATE.format(
                _join_data_path(config_base_path, FILES_TO_DOWNLOAD["policy_model_onnx"]["filename"]),
                _join_data_path(config_base_path, FILES_TO_DOWNLOAD["template_file"]["filename"]),
                _join_data_path(config_base_path, FILES_TO_DOWNLOAD["ringbreaker_model_onnx"]["filename"]),
                _join_data_path(config_base_path, FILES_TO_DOWNLOAD["ringbreaker_templates"]["filename"]),
                _join_data_path(config_base_path, FILES_TO_DOWNLOAD["filter_policy_onnx"]["filename"]),
                _join_data_path(config_base_path, FILES_TO_DOWNLOAD["stock"]["filename"]),
            )
        )
    print("Configuration file written to config.yml")


if __name__ == "__main__":
    main()
