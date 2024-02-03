import pandas as pd
from toplogger import TopLogger
from toplogger.utils import (
    NUM2FRENCHGRADE,
    list2dict,
    get_gym_holds_dict,
    get_gym_setters_dict,
)


def json_normalize(df, col):
    return (
        df.reset_index(drop=True)
        .assign(**pd.json_normalize(df[col]).add_prefix(f"{col}_"))
        .drop(columns=[col])
    )


def get_user_master_tables(user_id):
    tl = TopLogger()
    ascends = tl.user_ascends(user_id).includes("climb").execute()
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
        .query("topped == True")
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
            grade_string=lambda x: x["climb_grade"]
            .astype(str)
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


def get_gym_climbs(gym_id):
    tl = TopLogger()
    climbs = tl.climbs(gym_id).execute()
    gym_holds = get_gym_holds_dict(gym_id)
    gym_setters = get_gym_setters_dict(gym_id)

    df_climbs = (
        pd.DataFrame(climbs)
        .query("lived == True")
        .astype({"setter_id": "Int64"})
        .assign(
            grade_str=lambda x: x["grade"].map(NUM2FRENCHGRADE.get).astype("string"),
            color=lambda x: x["hold_id"].map(lambda y: gym_holds[y]["brand"]),
            hexcolor=lambda x: x["hold_id"].map(lambda y: gym_holds[y]["color"]),
            setter=lambda x: x["setter_id"].map(
                lambda y: gym_setters.get(y, {"name": ""})["name"], na_action="ignore"
            ),
        )
        .astype(
            {
                "grade": float,
            }
        )
    )

    for gym_id in df_climbs.gym_id.unique():
        df_challenge = (
            pd.DataFrame(tl.groups(int(gym_id)).includes("climb_groups").execute())
            .explode("climb_groups")
            .pipe(json_normalize, col="climb_groups")
            .drop(
                columns=[
                    "gym_id",
                    "order",
                    "live",
                    "lived",
                    "climbs_type",
                    "score_system",
                    "approve_participation",
                    "split_gender",
                    "climb_groups_order",
                    "split_age",
                ]
            )
            .rename(columns={"name": "circuit_name"})
            .reset_index()
        )
        df_climbs = df_climbs.merge(
            df_challenge, how="left", left_on="id", right_on="climb_groups_climb_id"
        )
    return df_climbs.fillna({"circuit_name": "", "remarks": ""}).assign(
        number=lambda x: x.number.str.extract(
            r"(\d+)",
        )
        .fillna(-1)
        .astype(int),
    )
