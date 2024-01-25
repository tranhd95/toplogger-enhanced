import pandas as pd
from toplogger import TopLogger
from toplogger.utils import (
    NUM2FRENCHGRADE,
    list2dict,
)


def json_normalize(df, col):
    return df.assign(**pd.json_normalize(df[col]).add_prefix(f"{col}_")).drop(
        columns=[col]
    )


def get_user_master_tables(user_id):
    tl = TopLogger()
    ascends = (
        tl.user_ascends(user_id).includes("climb").filters({"used": True}).execute()
    )
    df_ascends = (
        pd.DataFrame(ascends)
        .pipe(json_normalize, col="climb")
        .fillna({"climb_setter_id": -1})
        .astype(
            {
                "climb_gym_id": int,
                "climb_hold_id": int,
                "climb_setter_id": int,
                "climb_grade": float,
            }
        )
        .assign(date_logged=lambda x: pd.to_datetime(x["date_logged"]))
    )
    gyms = {
        int(gym_id): (tl.gym(gym_id).includes("holds").includes("setters").execute())
        for gym_id in df_ascends.climb_gym_id.unique()
    }
    for _, gym in gyms.items():
        gym["holds"] = list2dict(gym["holds"], "id")
        gym["setters"] = list2dict(gym["setters"], "id")

    community_grades = []
    community_opinions = []
    toppers = []
    for ascend in df_ascends.itertuples():
        cs = tl.climb_stats(ascend.climb_gym_id, ascend.climb_id).execute()
        community_grades.append(cs["community_grades"])
        community_opinions.append(cs["community_opinions"])
        toppers.append(cs["toppers"])
    df_community_grades = pd.DataFrame(
        {
            "community_grade": community_grades,
            "gym_id": df_ascends.climb_gym_id,
            "climb_id": df_ascends.climb_id,
        }
    )
    df_community_opinions = pd.DataFrame(
        {
            "community_opinion": community_opinions,
            "gym_id": df_ascends.climb_gym_id,
            "climb_id": df_ascends.climb_id,
        }
    )
    df_toppers = (
        pd.DataFrame(
            {
                "topper": toppers,
                "gym_id": df_ascends.climb_gym_id,
                "climb_id": df_ascends.climb_id,
            }
        )
        .explode("topper")
        .reset_index(drop=True)
        .pipe(json_normalize, col="topper")
    )

    return (
        df_ascends.assign(
            grade_string=lambda x: x["climb_grade"].astype(str)
            .map(NUM2FRENCHGRADE.get)
            .astype("string"),
            color=lambda x: x.apply(
                lambda row: gyms[row["climb_gym_id"]]["holds"][row["climb_hold_id"]][
                    "brand"
                ],
                axis=1,
            ),
            hexcolor=lambda x: x.apply(
                lambda row: gyms[row["climb_gym_id"]]["holds"][row["climb_hold_id"]][
                    "color"
                ],
                axis=1,
            ),
            setter=lambda x: x.apply(
                lambda row: gyms[row["climb_gym_id"]]["setters"].get(
                    row["climb_setter_id"], {"name": ""}
                )["name"],
                axis=1,
            ),
        ),
        gyms,
        df_community_grades,
        df_community_opinions,
        df_toppers,
    )