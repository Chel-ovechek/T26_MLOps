from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import joblib
import mlflow
import mlflow.data
import pandas as pd

from mlops_team1.evaluate import classification_metrics
from mlops_team1.run_meta import (
    build_run_summary,
    environment_lines,
    git_commit,
    git_dirty,
    read_dvc_md5,
)
from mlops_team1.train import FEATURES, train_model
from mlops_team1.validate_data import split_cuts, validate_dataset

SPLIT_POLICY = "chronological-60-20-20"
TARGET_THRESHOLD_MINUTES = 15
PROBABILITY_THRESHOLD = 0.5
DEFAULT_HYPOTHESIS = "Базовая конфигурация RandomForest, гипотеза не задана."


def run_experiment(
    data_path: Path,
    contract_path: Path,
    experiment: str,
    n_estimators: int,
    max_depth: int,
    random_state: int,
    *,
    team_code: str = "team-1",
    hypothesis: str = DEFAULT_HYPOTHESIS,
) -> str:
    validation = validate_dataset(data_path, contract_path)
    if not validation["passed"]:
        raise ValueError("Набор не прошёл контракт данных")

    frame = pd.read_csv(data_path)
    frame["FlightDate"] = pd.to_datetime(frame["FlightDate"], errors="raise")
    frame = frame.sort_values("FlightDate", kind="stable").reset_index(drop=True)
    train_end, validation_end = split_cuts(frame["FlightDate"].tolist())
    train_frame = frame.iloc[:train_end].copy()
    validation_frame = frame.iloc[train_end:validation_end].copy()
    train_target = (train_frame["ArrDelay"] >= TARGET_THRESHOLD_MINUTES).astype(int)
    validation_target = (validation_frame["ArrDelay"] >= TARGET_THRESHOLD_MINUTES).astype(int)
    if validation_target.nunique() < 2:
        raise ValueError("Validation-период должен содержать оба класса")

    mlflow.set_experiment(experiment)
    with tempfile.TemporaryDirectory(prefix="mlops-lr4-") as temp_dir:
        temp = Path(temp_dir)
        model_path = temp / "model.joblib"
        train_model(
            data_path,
            model_path,
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
        )
        bundle = joblib.load(model_path)
        if bundle["split"] != {"train_end": train_end, "validation_end": validation_end}:
            raise ValueError("Границы разбиения в модели и в run не совпадают")
        probabilities = bundle["model"].predict_proba(validation_frame[FEATURES])[:, 1]
        scores = classification_metrics(
            validation_target.to_numpy(), probabilities, threshold=PROBABILITY_THRESHOLD
        )
        metrics = {f"validation_{name}": value for name, value in scores.items()}
        metrics["validation_positive_rate"] = float(validation_target.mean())

        split_manifest = {
            "policy": SPLIT_POLICY,
            "rows": len(frame),
            "train_rows": train_end,
            "validation_rows": validation_end - train_end,
            "test_rows": len(frame) - validation_end,
            "train_end": str(frame.iloc[train_end - 1]["FlightDate"].date()),
            "validation_end": str(frame.iloc[validation_end - 1]["FlightDate"].date()),
            "test_end": str(frame.iloc[-1]["FlightDate"].date()),
        }
        parameters = {
            "algorithm": "RandomForestClassifier",
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "random_state": random_state,
            "target_threshold_minutes": TARGET_THRESHOLD_MINUTES,
            "probability_threshold": PROBABILITY_THRESHOLD,
            "split_policy": SPLIT_POLICY,
            **{f"split_{key}": value for key, value in split_manifest.items() if key != "policy"},
        }
        tags = {
            "git.commit": git_commit(),
            "git.dirty": git_dirty(),
            "data.dvc_hash": read_dvc_md5(data_path),
            "data.sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
            "data.contract_version": validation["contract_version"],
            "split.policy": SPLIT_POLICY,
            "team.code": team_code,
            "validation.status": "candidate",
        }
        run_name = f"rf-depth-{max_depth}"

        files = {
            "split_manifest.json": json.dumps(split_manifest, ensure_ascii=False, indent=2),
            "metrics.json": json.dumps(metrics, ensure_ascii=False, indent=2),
            "validation_report.json": json.dumps(validation, ensure_ascii=False, indent=2),
            "run_summary.md": build_run_summary(
                run_name=run_name,
                hypothesis=hypothesis,
                parameters=parameters,
                metrics=metrics,
                split=split_manifest,
                tags=tags,
            ),
            "requirements.txt": "\n".join(environment_lines()) + "\n",
        }
        for name, text in files.items():
            (temp / name).write_text(text, encoding="utf-8", newline="\n")

        training_input = mlflow.data.from_pandas(
            train_frame.assign(target=train_target),
            source=data_path.as_posix(),
            name="flight-delay-train",
            targets="target",
        )
        validation_input = mlflow.data.from_pandas(
            validation_frame.assign(target=validation_target),
            source=data_path.as_posix(),
            name="flight-delay-validation",
            targets="target",
        )

        with mlflow.start_run(run_name=run_name) as run:
            mlflow.log_params(parameters)
            mlflow.log_metrics(metrics)
            mlflow.log_input(training_input, context="training")
            mlflow.log_input(validation_input, context="validation")
            mlflow.set_tags(tags)
            mlflow.log_artifact(str(model_path), artifact_path="model")
            for name in ("split_manifest.json", "metrics.json", "validation_report.json"):
                mlflow.log_artifact(str(temp / name), artifact_path="reports")
            mlflow.log_artifact(str(temp / "run_summary.md"), artifact_path="reports")
            mlflow.log_artifact(str(temp / "requirements.txt"), artifact_path="environment")
            return run.info.run_id


def main() -> None:
    parser = argparse.ArgumentParser(description="MLflow Tracking для учебного проекта")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--n-estimators", type=int, default=80)
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--team-code", default="team-1")
    parser.add_argument("--hypothesis", default=DEFAULT_HYPOTHESIS)
    args = parser.parse_args()
    run_id = run_experiment(
        args.data,
        args.contract,
        args.experiment,
        args.n_estimators,
        args.max_depth,
        args.random_state,
        team_code=args.team_code,
        hypothesis=args.hypothesis,
    )
    print(f"MLflow run_id: {run_id}")


if __name__ == "__main__":
    main()
