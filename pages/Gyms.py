from toplogger import TopLogger
import streamlit as st
import pandas as pd
from toplogger.utils import get_gym_holds_dict, get_gym_setters_dict, NUM2FRENCHGRADE, json_normalize
import plotly.express as px


tl = TopLogger()

gyms = {
    206: 'Hangár Brno',
    207: 'Hangár Ostrava',
}

gym_id = st.selectbox("Select gym", list(gyms.keys()), format_func=lambda x: gyms[x])

@st.cache_data
def data(gym_id):
    climbs = tl.climbs(gym_id).execute()
    gym_holds = get_gym_holds_dict(gym_id)
    gym_setters = get_gym_setters_dict(gym_id)

    return (
        pd.DataFrame(climbs)
        .query('lived == True')
        .astype({'setter_id': 'Int64'})
        .assign(
            grade_str=lambda x: x['grade'].map(NUM2FRENCHGRADE.get).astype('string'),
            color=lambda x: x['hold_id'].map(lambda y: gym_holds[y]['brand']),
            hexcolor=lambda x: x['hold_id'].map(lambda y: gym_holds[y]['color']),
            setter=lambda x: x['setter_id'].map(lambda y: gym_setters.get(y, {'name': ''})['name'], na_action='ignore'),
        )
        .astype(
            {
                'grade': float
            }
        )
    )

df_climbs = data(gym_id)

st.button("Force refresh", type="primary", on_click=lambda: data.clear())

# Alltime grade
fig = px.histogram(
    df_climbs.sort_values(by="grade"),
    x="grade_str",
    title=f"All-time grades distribution at {gyms[gym_id]}",
    labels={
        "grade_str": "Grade",
    },
)
fig.update_layout(yaxis_title="Number of routes")
st.plotly_chart(fig)

# Setters
fig = px.histogram(
    df_climbs,
    x="setter",
    title=f"All-time setters distribution at {gyms[gym_id]}",
    labels={
        "setter": "Setter",
    }
)
fig.update_xaxes(categoryorder='total descending')
fig.update_layout(yaxis_title="Number of routes")
st.plotly_chart(fig)

# Most fun routes

@st.cache_data
def opinions(df):
    community_grades = []
    community_opinions = []
    toppers = []
    for ascend in df.itertuples():
        cs = tl.climb_stats(gym_id, ascend.id).execute()
        community_grades.append(cs["community_grades"])
        community_opinions.append(cs["community_opinions"])
        toppers.append(cs["toppers"])
    return df.assign(
        community_grade=community_grades,
        community_opinion=community_opinions,
    )

df_climbs = opinions(df_climbs)

df_opinions = (
    df_climbs
    .explode('community_opinion')
    .reset_index()
    .pipe(json_normalize, col='community_opinion')
    .query('community_opinion_votes > 0')
    .reset_index()
    .assign(
        stars=lambda x: x.community_opinion_stars * x.community_opinion_votes
    )
    .groupby('setter')
    .agg({'community_opinion_votes': 'sum', 'stars': 'sum'})
    .assign(
        average_stars=lambda x: x.stars / x.community_opinion_votes
    )
    .sort_values('average_stars')
    .reset_index()
)
fig = px.histogram(
    df_opinions,
    y="average_stars",
    x="setter",
    title=f"All-time routes average opinion by setter",
    labels={
        "average_stars": "Average opinion (1-5 stars)",
        "setter": "Setter"
    }
)
fig.update_xaxes(categoryorder='total descending')
fig.update_layout(yaxis_title="1-5 Opinion")
fig.update_layout(yaxis_range=[3.5,5])
st.plotly_chart(fig)

from itertools import repeat, chain
import numpy as np

df_setter_grade_diff = (
    df_climbs
    .reset_index()
    .assign(
        community_grade=lambda x: x.community_grade.apply(lambda grades: [float(g['grade']) for g in grades for _ in range(g['count'])])
    )
    .assign(
        community_grade=lambda x: x.apply(lambda row: np.mean(row['community_grade']) if len(row['community_grade']) > 0 else row['grade'], axis=1),
        grade_diff=lambda x: x.grade - x.community_grade
    )
    .groupby('setter')
    .grade_diff
    .describe()
    .sort_values(by='count', ascending=False)
    .iloc[:, 1:]
)

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go


plt.title('Positive = setter grades harder than community')
fig = sns.heatmap(
    df_setter_grade_diff.iloc[:, 1:],
    annot=True,
    center=0.,
    vmin=-1.,
    vmax=1.0,
    linewidth=.5,
)
st.pyplot(fig.figure)

# fig = go.Figure(data=go.Heatmap(
#         z=df_setter_grade_diff,
#         x=df_setter_grade_diff.columns,
#         y=df_setter_grade_diff.index,
#         text=df_setter_grade_diff.values,
#         colorscale='Viridis'))

# st.plotly_chart(fig)


