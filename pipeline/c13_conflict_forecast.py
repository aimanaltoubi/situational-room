"""Country-level ACLED conflict forecasting stage."""

from dataclasses import dataclass
from datetime import timedelta

import pandas as pd


@dataclass(frozen=True)
class ConflictForecastContext:
    acled_data: pd.DataFrame
    acled_cutoff: pd.Timestamp
    war_start: pd.Timestamp
    max_runtime_secs: int = 300
    max_models: int = 10
    seed: int = 42


@dataclass(frozen=True)
class ConflictForecastResult:
    predictions: pd.DataFrame
    country_risks: pd.DataFrame
    target_week: pd.Timestamp
    model_id: str
    cross_validation_auc: float
    training_rows: int


class H2OConflictForecastStage:
    """Train an H2O AutoML classifier and return country conflict risks."""

    def __init__(self, h2o_module=None, automl_class=None):
        if h2o_module is None or automl_class is None:
            import h2o as h2o_module
            from h2o.automl import H2OAutoML as automl_class

        self._h2o = h2o_module
        self._automl_class = automl_class

    def run(self, context: ConflictForecastContext) -> ConflictForecastResult:
        df = context.acled_data.copy()
        df["WEEK"] = pd.to_datetime(df["WEEK"])
        df_war = df[df["WEEK"] >= context.war_start].copy()

        weekly = df_war.groupby(["WEEK", "COUNTRY"]).agg(
            event_count=("EVENTS", "sum"),
            grid_lat=("CENTROID_LATITUDE", "mean"),
            grid_lon=("CENTROID_LONGITUDE", "mean"),
            airstrike=("SUB_EVENT_TYPE", lambda values: df_war.loc[values.index, "EVENTS"][
                df_war.loc[values.index, "SUB_EVENT_TYPE"] == "Air/drone strike"
            ].sum()),
            shelling=("SUB_EVENT_TYPE", lambda values: df_war.loc[values.index, "EVENTS"][
                df_war.loc[values.index, "SUB_EVENT_TYPE"] == "Shelling/artillery/missile attack"
            ].sum()),
            armed_clash=("SUB_EVENT_TYPE", lambda values: df_war.loc[values.index, "EVENTS"][
                df_war.loc[values.index, "SUB_EVENT_TYPE"] == "Armed clash"
            ].sum()),
            ied=("SUB_EVENT_TYPE", lambda values: df_war.loc[values.index, "EVENTS"][
                df_war.loc[values.index, "SUB_EVENT_TYPE"] == "Remote explosive/landmine/IED"
            ].sum()),
        ).reset_index()
        weekly["has_conflict"] = (weekly["event_count"] > 0).astype(int)

        countries = sorted(weekly["COUNTRY"].unique())
        weeks = sorted(weekly["WEEK"].unique())
        country_coords = weekly.groupby("COUNTRY").agg(
            lat=("grid_lat", "mean"), lon=("grid_lon", "mean")
        ).to_dict("index")
        panel = pd.DataFrame([
            {
                "WEEK": week,
                "COUNTRY": country,
                "grid_lat": country_coords.get(country, {}).get("lat", 0),
                "grid_lon": country_coords.get(country, {}).get("lon", 0),
            }
            for country in countries
            for week in weeks
        ])
        panel = panel.merge(
            weekly[["WEEK", "COUNTRY", "event_count", "has_conflict", "airstrike",
                    "shelling", "armed_clash", "ied"]],
            on=["WEEK", "COUNTRY"], how="left",
        )
        count_columns = ["event_count", "has_conflict", "airstrike", "shelling", "armed_clash", "ied"]
        panel[count_columns] = panel[count_columns].fillna(0).astype(int)
        panel = panel.sort_values(["COUNTRY", "WEEK"]).reset_index(drop=True)

        groups = panel.groupby("COUNTRY")
        source_columns = {
            "events": "event_count", "conflict": "has_conflict", "air": "airstrike",
            "shell": "shelling", "clash": "armed_clash",
        }
        for lag in [1, 2]:
            for feature, source in source_columns.items():
                panel[f"tlag_{lag}w_{feature}"] = groups[source].shift(lag)
        panel["wow_events"] = groups["event_count"].diff()
        panel["wow_air"] = groups["airstrike"].diff()
        panel["cum_events"] = groups["event_count"].cumsum().shift(1)
        panel["cum_air"] = groups["airstrike"].cumsum().shift(1)

        neighbors = {
            "Iran": ["Iraq", "Kuwait", "Bahrain", "Qatar", "United Arab Emirates", "Oman", "Saudi Arabia"],
            "Iraq": ["Iran", "Kuwait", "Syria", "Jordan", "Saudi Arabia"],
            "Israel": ["Lebanon", "Syria", "Jordan", "Palestine"],
            "Lebanon": ["Israel", "Syria"],
            "Syria": ["Lebanon", "Israel", "Jordan", "Iraq"],
            "Jordan": ["Israel", "Syria", "Iraq", "Saudi Arabia"],
            "Saudi Arabia": ["Iraq", "Kuwait", "Bahrain", "Qatar", "United Arab Emirates", "Oman", "Jordan", "Yemen"],
            "Kuwait": ["Iraq", "Iran", "Saudi Arabia"],
            "Bahrain": ["Saudi Arabia", "Qatar", "Iran"],
            "Qatar": ["Saudi Arabia", "Bahrain", "United Arab Emirates", "Iran"],
            "United Arab Emirates": ["Saudi Arabia", "Qatar", "Oman", "Iran"],
            "Oman": ["Saudi Arabia", "United Arab Emirates", "Yemen", "Iran"],
            "Yemen": ["Saudi Arabia", "Oman"],
            "Palestine": ["Israel"],
        }
        panel["splag_events"] = 0.0
        panel["splag_conflict"] = 0.0
        for week in weeks:
            week_mask = panel["WEEK"] == week
            week_data = panel[week_mask].set_index("COUNTRY")
            for country in countries:
                country_neighbors = neighbors.get(country, [])
                if country_neighbors:
                    neighbor_data = week_data[week_data.index.isin(country_neighbors)]
                    if not neighbor_data.empty:
                        country_mask = week_mask & (panel["COUNTRY"] == country)
                        panel.loc[country_mask, "splag_events"] = neighbor_data["event_count"].mean()
                        panel.loc[country_mask, "splag_conflict"] = neighbor_data["has_conflict"].mean()

        country_ids = {country: index for index, country in enumerate(countries)}
        panel["country_fe"] = panel["COUNTRY"].map(country_ids)
        panel["week_num"] = panel.groupby("WEEK").ngroup()

        features = [
            "tlag_1w_events", "tlag_1w_conflict", "tlag_1w_air", "tlag_1w_shell", "tlag_1w_clash",
            "tlag_2w_events", "tlag_2w_conflict", "tlag_2w_air", "tlag_2w_shell", "tlag_2w_clash",
            "wow_events", "wow_air", "cum_events", "cum_air", "splag_events", "splag_conflict",
            "country_fe", "week_num", "grid_lat", "grid_lon",
        ]
        target = "has_conflict"
        target_week = context.acled_cutoff + timedelta(days=14)
        train_df = panel[panel[features].notna().all(axis=1)].copy()
        train_df[target] = train_df[target].astype("category")

        pred_base = panel[panel["WEEK"] == panel["WEEK"].max()].copy()
        pred_base["WEEK"] = target_week
        pred_base["week_num"] = pred_base["week_num"] + 1
        last_week = panel[panel["WEEK"] == panel["WEEK"].max()].set_index("COUNTRY")
        for feature, source in source_columns.items():
            pred_base[f"tlag_2w_{feature}"] = pred_base[f"tlag_1w_{feature}"]
            pred_base[f"tlag_1w_{feature}"] = pred_base["COUNTRY"].map(last_week[source]).fillna(0)
        pred_base["wow_events"] = 0
        pred_base["wow_air"] = 0
        pred_base["grid_id"] = pred_base.apply(
            lambda row: f"{row.grid_lat:.2f}_{row.grid_lon:.2f}", axis=1
        )
        pred_base["ADMIN1"] = pred_base["COUNTRY"]
        base_activity = panel[panel["WEEK"] == panel["WEEK"].min()].set_index("COUNTRY")["event_count"]

        self._h2o.init(max_mem_size="4G")
        try:
            train_h2o = self._h2o.H2OFrame(train_df[features + [target]])
            train_h2o[target] = train_h2o[target].asfactor()
            pred_h2o = self._h2o.H2OFrame(pred_base[features])
            automl = self._automl_class(
                max_runtime_secs=context.max_runtime_secs,
                max_models=context.max_models,
                seed=context.seed,
                sort_metric="AUC",
                balance_classes=True,
                nfolds=3,
                keep_cross_validation_predictions=True,
            )
            automl.train(x=features, y=target, training_frame=train_h2o)
            best = automl.leader
            cross_validation_auc = best.auc(xval=True)
            predictions = best.predict(pred_h2o).as_data_frame()
        finally:
            self._h2o.shutdown(prompt=False)

        pred_base = pred_base.reset_index(drop=True)
        pred_base["prob_conflict"] = predictions["p1"].values
        bins = [0, 0.25, 0.5, 0.75, 1.0]
        labels = ["Low", "Medium", "High", "Very High"]
        pred_base["confidence_tier"] = pd.cut(pred_base["prob_conflict"], bins=bins, labels=labels)
        pred_base["early_activity"] = pred_base["COUNTRY"].map(base_activity).fillna(0)
        pred_base["is_new_emergence"] = (
            (pred_base["prob_conflict"] >= 0.6) & (pred_base["early_activity"] < 5)
        ).astype(int)

        country_risks = pred_base[["COUNTRY", "prob_conflict", "grid_lat", "grid_lon"]].copy()
        country_risks = country_risks.rename(columns={"prob_conflict": "mean_prob"})
        country_risks["risk_level"] = pd.cut(country_risks["mean_prob"], bins=bins, labels=labels)
        country_risks["total_grids"] = 1
        country_risks["high_risk_grids"] = (country_risks["mean_prob"] >= 0.5).astype(int)
        country_risks["max_prob"] = country_risks["mean_prob"]
        country_risks = country_risks.sort_values("mean_prob", ascending=False)

        return ConflictForecastResult(
            predictions=pred_base,
            country_risks=country_risks,
            target_week=target_week,
            model_id=best.model_id,
            cross_validation_auc=cross_validation_auc,
            training_rows=len(train_df),
        )