import hashlib
import json
import os
import subprocess
from sqlite3 import DatabaseError
from typing import Union
from urllib import parse

import pandas as pd
import streamlit as st

from db import _get_connector, add_row, get_table

TABLE = "url_table"
DEFAULT_HASH_LENGTH = 10
BASE_URL = "https://streamlit-widget-url-sync{branch}-e3jbxxj6ja-ue.a.run.app"

Params = dict[str, Union[str, list[str]]]


def _create_url_table():
    """
    Create a table in the database that will be used to store the mapping
    from short url to long url
    """
    conn = _get_connector()
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            hash TEXT PRIMARY KEY,
            params TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def get_url_table_data() -> pd.DataFrame:
    try:
        return get_table(TABLE)
    except DatabaseError:
        _create_url_table()
        return get_table(TABLE)


def get_hash(data: str, length: int = DEFAULT_HASH_LENGTH) -> str:
    """
    Given a string representation of data, return a length-characters-long string hash
    """
    return hashlib.md5(data.encode()).hexdigest()[:length]


def get_params() -> Params:
    """
    If the item only contains one string, just return it. Otherwise, return a list.
    """
    raw_params = st.experimental_get_query_params()

    params: Params = {}

    for key, value in raw_params.items():
        if len(value) == 1:
            params[key] = value[0]
        else:
            params[key] = value

    return params


def get_hash_from_params(params: Params = None) -> str:
    if params is None:
        params = get_params()
    return get_hash(json.dumps(params))


def get_params_from_hash(hash: str) -> Params:
    df = get_url_table_data()
    return json.loads(df[df["hash"] == hash].params.values[0])


def is_hash_in_table(hash: str) -> bool:
    df = get_url_table_data()
    return hash in df.hash.values


def save_hash_if_not_exists(params: Params = None) -> str:
    if params is None:
        params = get_params()
    hash = get_hash_from_params(params)
    if not is_hash_in_table(hash):
        add_row(
            TABLE,
            {"hash": hash, "params": json.dumps(params)},
        )
    return hash


def get_current_branch() -> str:
    return (
        subprocess.check_output(["git", "branch", "--show-current"], cwd=os.getcwd())
        .decode("utf-8")
        .strip()
    )


def get_short_url_from_hash(hash: str) -> str:
    branch = get_current_branch()

    if branch != "main":
        base_url = BASE_URL.format(branch="-" + branch)
    else:
        base_url = BASE_URL.format(branch="")

    return base_url + "?" + parse.urlencode({"q": hash})


def get_short_url_button():
    if st.button("Get short url"):
        hash = save_hash_if_not_exists()
        url = get_short_url_from_hash(hash)
        st.write(url)


def expand_short_url():
    query_params = st.experimental_get_query_params()
    if set(query_params.keys()) == {"q"}:
        short_hash = query_params["q"][0]
        try:
            query_params = get_params_from_hash(short_hash)
            st.experimental_set_query_params(**query_params)
        except IndexError:
            st.error(f"Invalid short url: {short_hash}")
