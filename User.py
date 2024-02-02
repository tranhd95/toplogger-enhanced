import streamlit as st
import pandas as pd
import seaborn as sns
from toplogger.analysis import get_user_master_tables
from toplogger.utils import NUM2FRENCHGRADE
from toplogger import TopLogger
import plotly.express as px
import plotly.graph_objects as go
import re

@st.cache_data
def cached(user_id):
    tl = TopLogger()
    user = tl.user(user_id).execute()
    return *get_user_master_tables(user_id), user

RE_UID = re.compile('^https://app.toplogger.nu/.*uid=(\d+).*|^(\d+)$')
def parse_user_id(string):
    user_id_str = None
    if match := RE_UID.search(string):
        user_id_str = next((m for m in match.groups() if m), None)
    if not user_id_str:
        st.write("Enter your TopLogger's user ID or whole TopLogger's profile URL:")
        return None
    else:
        return int(user_id_str)

sns.set_theme(style="whitegrid")
user_id_input = st.text_input("Enter your TopLogger's user ID or whole TopLogger's profile URL:")
if user_id_input:
    user_id = parse_user_id(user_id_input)
else:
    user_id = None

if user_id:
    st.button("Force refresh", type="primary", on_click=lambda: cached.clear())
    with st.spinner(text="In progress"):
        (
            df_ascends,
            gyms,
            df_community_grades,
            df_community_opinions,
            df_toppers,
            user
        ) = cached(user_id)

        st.markdown(f'''
                    <h1 style="text-align: center">{user['first_name']} {user['last_name']}</h1>
                    <div style="text-align: center"><img src="{user['avatar']}" /></div>
                    ''', unsafe_allow_html=True)
        
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