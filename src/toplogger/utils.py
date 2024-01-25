from typing import List, Any
import pandas as pd
from .toplogger import TopLogger

# https://github.com/rubenvanerk/toplogger-h2h/blob/5d434ae01e837c9cced84a403e19045338edeb2c/config/grades.php#L18
NUM2FRENCHGRADE = {
    "2.0": "?",
    "2.17": "2⁺",
    "2.33": "2ʙ",
    "2.5": "2ʙ⁺",
    "2.66": "2ᴄ",
    "2.67": "2ᴄ",
    "2.75": "2⁺",
    "2.83": "2ᴄ⁺",
    "3.0": "3ᴀ",
    "3.17": "3ᴀ⁺",
    "3.33": "3ʙ",
    "3.5": "3ʙ⁺",
    "3.66": "3ᴄ",
    "3.67": "3ᴄ",
    "3.83": "3ᴄ⁺",
    "4.0": "4ᴀ",
    "4.17": "4ᴀ⁺",
    "4.33": "4ʙ",
    "4.5": "4ʙ⁺",
    "4.66": "4ᴄ",
    "4.67": "4ᴄ",
    "4.83": "4ᴄ⁺",
    "5.0": "5ᴀ",
    "5.17": "5ᴀ⁺",
    "5.33": "5ʙ",
    "5.5": "5ʙ⁺",
    "5.66": "5ᴄ",
    "5.67": "5ᴄ",
    "5.83": "5ᴄ⁺",
    "6.0": "6ᴀ",
    "6.17": "6ᴀ⁺",
    "6.33": "6ʙ",
    "6.5": "6ʙ⁺",
    "6.66": "6ᴄ",
    "6.67": "6ᴄ",
    "6.83": "6ᴄ⁺",
    "7.0": "7ᴀ",
    "7.17": "7ᴀ⁺",
    "7.33": "7ʙ",
    "7.5": "7ʙ⁺",
    "7.66": "7ᴄ",
    "7.67": "7ᴄ",
    "7.83": "7ᴄ⁺",
    "8.0": "8ᴀ",
    "8.17": "8ᴀ⁺",
    "8.33": "8ʙ",
    "8.5": "8ʙ⁺",
    "8.66": "8ᴄ",
    "8.67": "8ᴄ",
    "8.83": "8ᴄ⁺",
    "9.0": "9ᴀ",
    "9.17": "9ᴀ⁺",
    "9.33": "9ʙ",
    "9.5": "9ʙ⁺",
    "9.66": "9ᴄ",
    "9.67": "9ᴄ",
    "9.83": "9ᴄ⁺",
    "10.0": "10ᴀ",
}


def find_gyms_by_name(name: str) -> List[Any]:
    """Find gym ids by name."""
    gyms = TopLogger().gyms().execute()
    return [gym for gym in gyms if name.lower() in gym["name"].lower()]


def get_gym_holds_dict(gym_id: int) -> List[dict[int, Any]]:
    """Get holds for gym."""
    holds = TopLogger().gym(gym_id).includes("holds").execute()["holds"]
    return {hold["id"]: hold for hold in holds}


def get_gym_setters_dict(gym_id: int) -> List[dict[int, Any]]:
    """Get setters for gym."""
    setters = TopLogger().gym(gym_id).includes("setters").execute()["setters"]
    return {setter["id"]: setter for setter in setters}


def list2dict(lst: List[Any], col="id") -> dict[Any, Any]:
    """Convert list to dict."""
    return {item[col]: item for item in lst}


def json_normalize(df, col):
    return df.assign(**pd.json_normalize(df[col]).add_prefix(f"{col}_")).drop(
        columns=[col]
    )
