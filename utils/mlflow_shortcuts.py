import mlflow
from mlflow.entities import Run


def get_or_create_experiment_by_name(name: str) -> str:
    """
    Returns an experiment_id by experiment name.
    If experiment with provided name doesn't exist creates new one.
    """
    experiment = mlflow.get_experiment_by_name(name)

    if not experiment:
        return mlflow.create_experiment(name)

    return experiment.experiment_id


def create_unique_run_by_name(experiment_name: str, run_name: str) -> str:
    """
    Deletes all existing runs with the given `run_name` and creates a new one.
    Creates an experiment if it doesn't exist.
    Returns a `run_id` of newly created run.
    """
    experiment_id = get_or_create_experiment_by_name(experiment_name)

    for exisiting_run in mlflow.search_runs(
        experiment_ids=[experiment_id],
        filter_string=f'run_name = "{run_name}"',
        output_format='list'
    ):
        mlflow.delete_run(exisiting_run.info.run_id)  # type: ignore

    with mlflow.start_run(experiment_id=experiment_id,
                          run_name=run_name) as new_run:
        return new_run.info.run_id


def get_run_by_name(experiment_name: str, run_name: str) -> Run | None:
    """Returns latest `Run` with given name."""
    experiment = mlflow.get_experiment_by_name(experiment_name)

    if not experiment:
        return None

    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string=f'run_name = "{run_name}"',
        order_by=['start_time DESC'],
        output_format='list'
    )

    return runs[0] if runs else None  # type: ignore
