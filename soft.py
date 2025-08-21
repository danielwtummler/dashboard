import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

from utils import get_color

def extract_comp_data(comp: str) -> tuple[str, int]:
    """Extrae información de las competencias blandas. Retorna la competencia en cuestion y el nivel en formato tupla."""
    parts = comp.split("(")
    comp_str = " ".join(parts[:-1]).replace("Muy bajo", "").replace("Bajo", "").replace("Medio", "").replace("Alto", "").replace("Muy alto", "").strip()
    lower_thresh = int(parts[-1].split()[0])
    thresh_map = {1 : 1, 11 : 2, 31 : 3, 70 : 4, 90 : 5}
    return comp_str, thresh_map[lower_thresh]

def get_required_levels(row: pd.Series, required_skills_col: str):
    """Callback que extrae los niveles de la competencias necesarias, proporcionado el nombre de la columna que las guarda."""
    required_skills = [extract_comp_data(comp) for comp in row[required_skills_col]]
    return {skill: level for skill, level in required_skills}

def score_dataframe(df: pd.DataFrame, actual_skills_col="competencias_blandas", required_skills_col="competencias_blandas_necesarias"):
    """Calcula el promedio de las competencias blandas y los compara con el nivel necesario."""

    # Calculate the required skill levels for each row
    df['required_levels'] = df.apply(lambda row: get_required_levels(row, required_skills_col), axis=1)

    # Extract all soft skills and their levels
    all_skills = []
    for _, row in df.iterrows():
        for comp in row[actual_skills_col]:
            skill, level = extract_comp_data(comp)
            all_skills.append((skill, level))

    # Calculate the average level for each soft skill
    skill_levels = {}
    for skill, level in all_skills:
        if skill in skill_levels:
            skill_levels[skill].append(level)
        else:
            skill_levels[skill] = [level]

    average_levels = {skill: np.mean(levels) for skill, levels in skill_levels.items()}

    std_dev_levels = {skill: np.std(levels) for skill, levels in skill_levels.items()}

    # Find the "average" required level
    required_levels = {}
    for _, row in df.iterrows():
        for skill, level in row['required_levels'].items():
            if skill in required_levels:
                required_levels[skill].append(level)
            else:
                required_levels[skill] = [level]

    most_common_required = {skill: max(set(levels), key=levels.count) for skill, levels in required_levels.items()}

    return average_levels, std_dev_levels, most_common_required

def get_soft_skills_scores_figs(df):
    """Toma un dataframe filtrado y hace un plot de las competencias blandas de cada candidato."""
    df_dropped = df.dropna(subset=["competencias_blandas", "competencias_blandas_necesarias"])
    average_levels, std_dev_levels, required_levels = score_dataframe(df_dropped)

    average_levels = {k: average_levels[k] if k in average_levels.keys() else 0 for k in required_levels.keys()}

    areas = [
        "Área intrapersonal",
        "Área interpersonal",
        "Área desarrollo de tareas",
        "Área entorno",
        "Área gerencial / management"
    ]

    figs = []

    for area in areas:
        req_lvls = {k.replace(area, "").strip() : v for k, v in required_levels.items() if area in k}
        avg_lvls = {k.replace(area, "").strip() : v for k, v in average_levels.items() if area in k}
        std_lvls = {k.replace(area, "").strip(): v for k, v in std_dev_levels.items() if area in k}
        
        colors = [get_color(avg_lvls[skill], req_lvls[skill])
                for skill in req_lvls]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=list(avg_lvls.keys()),
            y=list(avg_lvls.values()),
            # This is the key part for adding error bars
            error_y=dict(
                type='data',
                array=list(std_lvls.values()),
                visible=True,
                color='gray',  # Optional: style the error bars
                thickness=1.5
            ),
            # Use marker_color to pass your custom color list
            marker_color=colors
        ))
        
        # Update layout properties
        fig.update_layout(
            title_text=f"{area} (n={df_dropped.shape[0]})",
            yaxis_title='Nivel Promedio: Muy bajo (0) - Muy alto (4)',
            yaxis_range=[0, 6],
            showlegend=False # Hide legend as colors are informational
        )
        
        figs.append(fig)

    return figs