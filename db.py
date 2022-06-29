import sqlite3

import pandas as pd
import streamlit as st


def _get_connector() -> sqlite3.Connection:
    return sqlite3.connect("example.db")


def get_table(table: str) -> pd.DataFrame:
    """
    Pass a table name to get a dataframe of that table
    """
    conn = _get_connector()
    df = pd.read_sql(f"SELECT * FROM {table}", conn)
    conn.close()
    return df


def add_row(table: str, data: dict):
    conn = _get_connector()
    placeholders = ",".join(["?"] * len(data))
    conn.execute(
        f"INSERT INTO {table} {tuple(data.keys())} VALUES ({placeholders})",
        tuple(data.values()),
    )
    conn.commit()
    conn.close()


def query(sql: str):
    conn = _get_connector()
    df = pd.read_sql(sql, conn)
    conn.close()
    return df
