# app.py - POOK Talent X 集团总览 V3.0

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="POOK Talent X", layout="wide")

st.title("🎯 POOK 人才 X 招聘指挥中心")
st.markdown("### AI驱动人才增长指挥中心")

FILE_PATH = "data/2026招聘进度表汇总统计表.xlsx"


@st.cache_data
def load_data():
    demand = pd.read_excel(FILE_PATH, sheet_name="需求明细&岗位JD")
    progress = pd.read_excel(FILE_PATH, sheet_name="招聘进度明细")
    onboard = pd.read_excel(FILE_PATH, sheet_name="待入职表")
    return demand, progress, onboard


demand_df, progress_df, onboard_df = load_data()


def status_count(df, keyword):
    return df["招聘状态"].astype(str).str.contains(keyword, na=False).sum()


def map_business_block(project):
    project = str(project)

    if any(k in project for k in ["财务", "人事", "行政", "营销策略", "供应链管理中心", "总经办"]):
        return "中后台职能"
    if any(k in project for k in ["抖音", "直播", "兴趣", "短视频", "达人", "内容"]):
        return "兴趣电商"
    if any(k in project for k in ["即时零售", "闪电仓", "O2O"]):
        return "即时零售"
    if any(k in project for k in ["乐高", "AI教育", "教育", "生态"]):
        return "生态业务"

    return "货架电商"


def calc_cycle(row):
    start = row.get("需求提出日期")
    end = row.get("需求完成日期")

    if pd.isna(start):
        return None

    start = pd.to_datetime(start)

    if pd.isna(end):
        end = datetime.today()
    else:
        end = pd.to_datetime(end)

    return (end - start).days


demand_df["业务板块"] = demand_df["项目"].apply(map_business_block)
demand_df["招聘周期"] = demand_df.apply(calc_cycle, axis=1)

total_requirements = len(demand_df)
total_hc = demand_df["需求数量"].sum()
completed = status_count(demand_df, "完成")
ongoing = status_count(demand_df, "进行中|招聘中|进行")
completion_rate = round(completed / total_requirements * 100, 1)

avg_cycle = round(demand_df["招聘周期"].dropna().mean(), 1)

risk_df = demand_df[
    (demand_df["招聘周期"].notna())
    & (demand_df["招聘周期"] > 45)
    & (~demand_df["招聘状态"].astype(str).str.contains("完成", na=False))
].copy()

risk_count = len(risk_df)

onboard_df["入职日期"] = pd.to_datetime(onboard_df["入职日期"], errors="coerce")
onboard_df["OFFER时间"] = pd.to_datetime(onboard_df["OFFER时间"], errors="coerce")

current_month = datetime.today().month

monthly_offer = onboard_df[onboard_df["OFFER时间"].dt.month == current_month].shape[0]
monthly_onboard = onboard_df[onboard_df["入职日期"].dt.month == current_month].shape[0]


page = st.sidebar.radio(
    "导航",
    ["集团总览", "业务板块", "分公司分析", "岗位分析", "招聘团队", "人工智能分析官"]
)


if page == "集团总览":

    st.header("🏠 集团总览｜HRD驾驶舱")

    st.subheader("① 集团招聘健康度")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("需求条数", total_requirements)
    c2.metric("需求HC", int(total_hc))
    c3.metric("招聘中", ongoing)
    c4.metric("已完成", completed)

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("完成率", f"{completion_rate}%")
    c6.metric("超期风险岗位", risk_count)
    c7.metric("本月Offer", monthly_offer)
    c8.metric("平均招聘周期", f"{avg_cycle}天")

    st.markdown("---")

    st.subheader("② 业务板块红黄绿灯")

    block_summary = demand_df.groupby("业务板块").agg(
        需求条数=("岗位", "count"),
        需求HC=("需求数量", "sum"),
        招聘中=("招聘状态", lambda x: x.astype(str).str.contains("进行中|招聘中|进行", na=False).sum()),
        已完成=("招聘状态", lambda x: x.astype(str).str.contains("完成", na=False).sum()),
        平均周期=("招聘周期", "mean")
    ).reset_index()

    block_summary["完成率"] = (
        block_summary["已完成"] / block_summary["需求条数"] * 100
    ).round(1)

    block_summary["平均周期"] = block_summary["平均周期"].round(1)

    def health_status(rate):
        if rate >= 80:
            return "🟢 健康"
        elif rate >= 60:
            return "🟡 关注"
        else:
            return "🔴 风险"

    block_summary["健康状态"] = block_summary["完成率"].apply(health_status)

    st.dataframe(
        block_summary[
            ["业务板块", "健康状态", "需求条数", "需求HC", "招聘中", "已完成", "完成率", "平均周期"]
        ],
        use_container_width=True
    )

    fig_block = px.bar(
        block_summary,
        x="业务板块",
        y="完成率",
        text="完成率",
        title="各业务板块招聘完成率"
    )
    st.plotly_chart(fig_block, use_container_width=True)

    st.markdown("---")

    st.subheader("③ 超期岗位预警 TOP10")

    if not risk_df.empty:
        top_risk = risk_df.sort_values("招聘周期", ascending=False).head(10)

        show_cols = [
            "岗位", "业务板块", "项目", "职能", "职级",
            "招聘负责人", "需求数量", "推荐简历数", "招聘状态", "招聘周期", "备注"
        ]
        show_cols = [c for c in show_cols if c in top_risk.columns]

        st.dataframe(top_risk[show_cols], use_container_width=True)
    else:
        st.success("当前暂无超过45天且未完成的超期岗位。")

    st.markdown("---")

    st.subheader("④ 集团招聘漏斗")

    resume_count = len(progress_df)

    screened = (
        progress_df["简历筛选"].astype(str).str.contains("通过", na=False).sum()
        if "简历筛选" in progress_df.columns else 0
    )

    interview = (
        progress_df["所在环节"].astype(str).str.contains("面试", na=False).sum()
        if "所在环节" in progress_df.columns else 0
    )

    offer_count = onboard_df["OFFER时间"].notna().sum()
    onboarded = onboard_df["是否已入职"].fillna(0).astype(float).sum()

    funnel_df = pd.DataFrame({
        "环节": ["简历进入", "筛选通过", "进入面试", "Offer", "已入职"],
        "人数": [resume_count, screened, interview, offer_count, int(onboarded)]
    })

    fig_funnel = px.funnel(
        funnel_df,
        x="人数",
        y="环节",
        title="集团招聘漏斗"
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

    st.markdown("---")

    st.subheader("⑤ 招聘负责人工作负荷")

    team_summary = demand_df.groupby("招聘负责人").agg(
        负责需求数=("岗位", "count"),
        需求HC=("需求数量", "sum"),
        推荐简历数=("推荐简历数", "sum"),
        已完成=("招聘状态", lambda x: x.astype(str).str.contains("完成", na=False).sum()),
        招聘中=("招聘状态", lambda x: x.astype(str).str.contains("进行中|招聘中|进行", na=False).sum()),
        平均周期=("招聘周期", "mean")
    ).reset_index()

    team_summary["完成率"] = (
        team_summary["已完成"] / team_summary["负责需求数"] * 100
    ).round(1)

    team_summary["平均周期"] = team_summary["平均周期"].round(1)

    st.dataframe(
        team_summary.sort_values("负责需求数", ascending=False),
        use_container_width=True
    )

    fig_team = px.bar(
        team_summary.sort_values("负责需求数", ascending=False),
        x="招聘负责人",
        y="负责需求数",
        text="负责需求数",
        title="招聘负责人工作负荷"
    )
    st.plotly_chart(fig_team, use_container_width=True)

    st.markdown("---")

    st.subheader("⑥ AI分析官｜自动经营解读")

    highest_risk_block = block_summary.sort_values("完成率").iloc[0]["业务板块"]
    lowest_rate = block_summary.sort_values("完成率").iloc[0]["完成率"]

    risk_jobs = (
        "、".join(risk_df["岗位"].head(5).astype(str).tolist())
        if not risk_df.empty else "暂无明显超期岗位"
    )

    st.info(f"""
【集团招聘经营诊断】

截至目前，集团共有招聘需求 **{total_requirements}** 条，需求HC **{int(total_hc)}** 个。

当前已完成 **{completed}** 条，招聘中 **{ongoing}** 条，整体完成率为 **{completion_rate}%**，平均招聘周期为 **{avg_cycle}天**。

当前系统识别到超期风险岗位 **{risk_count}** 个，重点关注岗位包括：**{risk_jobs}**。

从业务板块看，当前完成率最低的板块为 **{highest_risk_block}**，完成率为 **{lowest_rate}%**，建议优先复盘该板块的人才供给情况、渠道有效性与业务反馈效率。

建议HRD重点关注：

1. 超过45天仍未完成的岗位；
2. 招聘完成率低于60%的业务板块；
3. 推荐简历数较低但招聘周期较长的岗位；
4. 招聘负责人之间的工作负荷差异；
5. Offer到入职的转化情况。
""")


elif page == "业务板块":
    st.header("📊 业务板块分析")

    selected_block = st.selectbox(
        "选择业务板块",
        ["全部"] + sorted(demand_df["业务板块"].dropna().unique().tolist())
    )

    df = demand_df.copy()
    if selected_block != "全部":
        df = df[df["业务板块"] == selected_block]

    st.dataframe(df, use_container_width=True)


elif page == "分公司分析":
    st.header("🏢 分公司分析")

    if "办公地点" in onboard_df.columns:
        location = st.selectbox(
            "选择办公地点",
            ["全部"] + sorted(onboard_df["办公地点"].dropna().astype(str).unique().tolist())
        )

        df = onboard_df.copy()
        if location != "全部":
            df = df[df["办公地点"].astype(str) == location]

        st.dataframe(df, use_container_width=True)
    else:
        st.warning("当前待入职表中未找到【办公地点】字段。")


elif page == "岗位分析":
    st.header("🎯 岗位分析")

    job = st.selectbox(
        "选择岗位",
        ["全部"] + sorted(demand_df["岗位"].dropna().astype(str).unique().tolist())
    )

    df = demand_df.copy()
    if job != "全部":
        df = df[df["岗位"].astype(str) == job]

    st.dataframe(df, use_container_width=True)

    if job != "全部":
        st.subheader("候选人池")
        candidate_df = progress_df[progress_df["岗位"].astype(str) == job]
        st.dataframe(candidate_df, use_container_width=True)


elif page == "招聘团队":
    st.header("👥 招聘团队")
    st.dataframe(team_summary, use_container_width=True)


elif page == "人工智能分析官":
    st.header("🤖 人工智能分析官")
    st.info("后续可接入自动日报、周报、风险预警和经营建议。")