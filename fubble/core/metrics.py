from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from fubble.database.models import Metric, MetricType, AggregationType


class MetricManager:
    """
    Manages the metrics registry and performs metric calculations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_metric(
        self,
        name: str,
        display_name: str,
        description: str,
        unit: str,
        metric_type: str,
        aggregation_type: str = "sum",
        formula: Optional[Dict[str, Any]] = None,
        display_properties: Optional[Dict[str, Any]] = None,
    ) -> Metric:
        """
        Creates a new metric in the registry.

        :param name: Unique identifier for the metric.
        :param display_name: Human-readable name.
        :param description: Description of what the metric measures.
        :param unit: The unit of measurement (e.g., "MB", "API calls").
        :param metric_type: Type of metric (counter, gauge, dimension, time, composite).
        :param aggregation_type: How to aggregate this metric (sum, max, min, avg, last).
        :param formula: For composite metrics, the formula to calculate it.
        :param display_properties: Properties for displaying the metric.
        :return: The created Metric object.
        """
        # Validate metric type
        if metric_type not in [t.value for t in MetricType]:
            raise ValueError(f"Invalid metric type: {metric_type}")

        # Validate aggregation type
        if aggregation_type not in [t.value for t in AggregationType]:
            raise ValueError(f"Invalid aggregation type: {aggregation_type}")

        # For composite metrics, formula is required
        if metric_type == MetricType.COMPOSITE and not formula:
            raise ValueError("Composite metrics require a formula")

        # Create the metric
        metric = Metric(
            name=name,
            display_name=display_name,
            description=description,
            unit=unit,
            type=metric_type,
            aggregation_type=aggregation_type,
            formula=formula,
            display_properties=display_properties or {},
        )

        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)

        return metric

    def get_metric(self, metric_id_or_name: Any) -> Optional[Metric]:
        """
        Gets a metric by ID or name.

        :param metric_id_or_name: Either the metric ID or name.
        :return: The Metric object if found, None otherwise.
        """
        if isinstance(metric_id_or_name, int):
            return self.db.query(Metric).filter(Metric.id == metric_id_or_name).first()
        else:
            return (
                self.db.query(Metric).filter(Metric.name == metric_id_or_name).first()
            )

    def get_all_metrics(self) -> List[Metric]:
        """
        Gets all metrics in the registry.

        :return: List of all Metric objects.
        """
        return self.db.query(Metric).all()

    def update_metric(
        self, metric_id: int, update_data: Dict[str, Any]
    ) -> Optional[Metric]:
        """
        Updates a metric's details.

        :param metric_id: The metric's ID.
        :param update_data: Dictionary of fields to update.
        :return: The updated Metric object if found, None otherwise.
        """
        metric = self.get_metric(metric_id)
        if not metric:
            return None

        # Update metric fields
        for key, value in update_data.items():
            if hasattr(metric, key) and key != "id":
                setattr(metric, key, value)

        metric.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(metric)

        return metric

    def delete_metric(self, metric_id: int) -> bool:
        """
        Deletes a metric from the registry.

        :param metric_id: The metric's ID.
        :return: True if successful, False otherwise.
        """
        metric = self.get_metric(metric_id)
        if not metric:
            return False

        try:
            self.db.delete(metric)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            return False

    def calculate_composite_metric(
        self,
        metric: Metric,
        input_values: Dict[str, float],
        execution_context: Dict[str, Any] = None,
    ) -> float:
        """
        Calculates the value of a composite metric based on its formula.

        :param metric: The composite metric to calculate.
        :param input_values: Dictionary mapping metric names to their values.
        :param execution_context: Additional context for formula execution.

        :return: The calculated value.
        """
        if metric.type != MetricType.COMPOSITE:
            raise ValueError(f"Metric {metric.name} is not a composite metric")

        formula = metric.formula
        if not formula:
            raise ValueError(f"Metric {metric.name} does not have a formula")

        # Get the formula type
        formula_type = formula.get("type")

        if formula_type == "arithmetic":
            # Simple arithmetic formula
            expression = formula.get("expression")
            if not expression:
                raise ValueError("Missing expression in formula")

            # Replace variable placeholders with actual values
            variables = formula.get("variables", {})
            expression_with_values = expression

            for var_name, var_config in variables.items():
                source_metric = var_config.get("metric")
                if source_metric in input_values:
                    # Replace the variable with the actual value
                    expression_with_values = expression_with_values.replace(
                        f"{{{var_name}}}", str(input_values[source_metric])
                    )
                else:
                    raise ValueError(f"Missing value for metric {source_metric}")

            # Evaluate the expression
            try:
                # TODO: use a safer expression parser.
                # This is a hack to get the formula to work, super unsafe,
                # I'm sorry if you're reading this.
                return eval(expression_with_values)
            except Exception as e:
                raise ValueError(f"Error evaluating formula: {str(e)}")

        elif formula_type == "function":
            # Custom function
            func_name = formula.get("function")

            # This is where you'd implement custom functions
            # For example:
            if func_name == "weighted_sum":
                weights = formula.get("weights", {})
                result = 0
                for metric_name, weight in weights.items():
                    if metric_name in input_values:
                        result += input_values[metric_name] * weight
                    else:
                        raise ValueError(f"Missing value for metric {metric_name}")
                return result

            raise ValueError(f"Unknown function: {func_name}")

        else:
            raise ValueError(f"Unknown formula type: {formula_type}")
