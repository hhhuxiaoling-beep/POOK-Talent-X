import pandas as pd

FILE_PATH = "data/2026招聘进度表汇总统计表.xlsx"

def load_data():

    demand = pd.read_excel(
        FILE_PATH,
        sheet_name="需求明细&岗位JD"
    )

    progress = pd.read_excel(
        FILE_PATH,
        sheet_name="招聘进度明细"
    )

    onboard = pd.read_excel(
        FILE_PATH,
        sheet_name="待入职表"
    )

    return demand, progress, onboard