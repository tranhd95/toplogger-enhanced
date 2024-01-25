import streamlit as st
import pandas as pd
import seaborn as sns
from toplogger.analysis import get_user_master_tables
import plotly.express as px
import plotly.graph_objects as go
from toplogger.utils import NUM2FRENCHGRADE
import re


sns.set_theme(style="whitegrid")
RE_NUMBER = re.compile('\d+')
user_id = st.text_input("Enter your TopLogger's user ID or whole TopLogger's profile URL:")
if user_id:
    try:
        user_id = RE_NUMBER.findall(user_id)[0]
        user_id = int(user_id)
    except ValueError:
        st.write("Must be a number.")


@st.cache_data
def cached(user_id):
    return get_user_master_tables(user_id)


if user_id:
    with st.spinner(text="In progress"):
        (
            df_ascends,
            gyms,
            df_community_grades,
            df_community_opinions,
            df_toppers,
        ) = cached(user_id)

    st.title("All-time stats")

    df_major_vote = df_community_grades.assign(
        major_vote_grade=lambda x: x.community_grade.apply(
            lambda y: sorted(y, key=lambda z: z["count"])[-1]["grade"]
        ),
        grade_string=lambda x: x.major_vote_grade.apply(NUM2FRENCHGRADE.get),
        grade_type="community",
    ).sort_values(by="major_vote_grade")

    df_ascends = df_ascends.assign(grade_type="setter")
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            histfunc="count",
            x=df_major_vote.grade_string,
            y=df_major_vote.grade_type,
            name="Community grade (major vote)",
        )
    )
    fig.add_trace(
        go.Histogram(
            histfunc="count",
            x=df_ascends.grade_string,
            y=df_ascends.grade_type,
            name="Setter's grade",
        )
    )
    fig.update_layout(title_text="Grade distribution of topped routes")
    st.plotly_chart(fig)

    st.title("Stats by session")

    session_dates = sorted(
        (df_ascends.assign(date=lambda x: x.date_logged.dt.date).date.unique()),
        reverse=True,
    )
    selected_date = st.selectbox(
        "Select session date",
        session_dates,
        format_func=lambda x: x.strftime("%a %d/%m/%Y"),
    )

    df_date = df_ascends[df_ascends.date_logged.dt.date == selected_date]

    fig = px.histogram(
        df_date.sort_values(by="climb_grade"),
        x="grade_string",
        title=f"Grades topped at {selected_date}",
        labels={
            "grade_string": "Grade",
        },
    )
    fig.update_layout(yaxis_title="Number of tops")
    st.plotly_chart(fig)
    # f"background-color: {x}"

    df = df_date.sort_values('climb_grade', ascending=False).assign(index=lambda x: range(1, len(x)+1)).set_index('index')[['hexcolor', 'grade_string', 'climb_average_opinion', 'setter']]
    styler = df.style.map(lambda x: f"background-color: {x}; color: {x}; opacity: 0.99",subset=['hexcolor'])
    st.table(
        styler
    )