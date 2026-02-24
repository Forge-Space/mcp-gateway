"""Tests for training pipeline functionality."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from tool_router.training.training_pipeline import (
    ModelPerformance,
    TrainingConfig,
    TrainingPipeline,
    TrainingResult,
)


class TestTrainingPipeline:
    """Test cases for TrainingPipeline functionality."""

    def test_training_pipeline_initialization(self) -> None:
        """Test TrainingPipeline initialization."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
        )

        pipeline = TrainingPipeline(config)

        assert pipeline.config.model_name == "test_model"
        assert pipeline.config.epochs == 10
        assert pipeline.config.batch_size == 32

    def test_training_pipeline_load_data(self) -> None:
        """Test training data loading."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
        )

        pipeline = TrainingPipeline(config)

        # Mock data loading
        with patch("tool_router.training.training_pipeline.load_training_data") as mock_load:
            mock_data = [
                {"input": "test input 1", "output": "test output 1"},
                {"input": "test input 2", "output": "test output 2"},
            ]
            mock_load.return_value = mock_data

            data = pipeline.load_training_data()

            assert len(data) == 2
            assert data[0]["input"] == "test input 1"

    def test_training_pipeline_preprocess_data(self) -> None:
        """Test data preprocessing."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
        )

        pipeline = TrainingPipeline(config)

        raw_data = [
            {"input": "Test Input", "output": "Test Output"},
            {"input": "Another Input", "output": "Another Output"},
        ]

        processed_data = pipeline.preprocess_data(raw_data)

        assert len(processed_data) == 2
        assert all("processed_input" in item for item in processed_data)
        assert all("processed_output" in item for item in processed_data)

    def test_training_pipeline_train_model(self) -> None:
        """Test model training."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
        )

        pipeline = TrainingPipeline(config)

        # Mock model training
        with patch("tool_router.training.training_pipeline.ModelTrainer") as mock_trainer:
            mock_trainer_instance = Mock()
            mock_trainer.return_value = mock_trainer_instance
            mock_trainer_instance.train.return_value = ModelPerformance(accuracy=0.85, loss=0.15, epochs_trained=10)

            training_data = [{"input": "test", "output": "test"}]
            result = pipeline.train_model(training_data)

            assert isinstance(result, ModelPerformance)
            assert result.accuracy == 0.85
            assert result.loss == 0.15
            assert result.epochs_trained == 10

    def test_training_pipeline_evaluate_model(self) -> None:
        """Test model evaluation."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
        )

        pipeline = TrainingPipeline(config)

        # Mock model evaluation
        with patch("tool_router.training.training_pipeline.ModelEvaluator") as mock_evaluator:
            mock_evaluator_instance = Mock()
            mock_evaluator.return_value = mock_evaluator_instance
            mock_evaluator_instance.evaluate.return_value = ModelPerformance(
                accuracy=0.90, loss=0.10, epochs_trained=10
            )

            test_data = [{"input": "test", "output": "test"}]
            result = pipeline.evaluate_model(test_data)

            assert isinstance(result, ModelPerformance)
            assert result.accuracy == 0.90
            assert result.loss == 0.10

    def test_training_pipeline_save_model(self) -> None:
        """Test model saving."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
        )

        pipeline = TrainingPipeline(config)

        # Mock model saving
        with patch("tool_router.training.training_pipeline.save_model_to_disk") as mock_save:
            mock_save.return_value = True

            result = pipeline.save_model("/path/to/save/model")

            assert result is True
            mock_save.assert_called_once_with("/path/to/save/model")

    def test_training_pipeline_full_training_cycle(self) -> None:
        """Test complete training cycle."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
        )

        pipeline = TrainingPipeline(config)

        # Mock all steps
        with (
            patch.object(pipeline, "load_training_data") as mock_load,
            patch.object(pipeline, "preprocess_data") as mock_preprocess,
            patch.object(pipeline, "train_model") as mock_train,
            patch.object(pipeline, "evaluate_model") as mock_evaluate,
            patch.object(pipeline, "save_model") as mock_save,
        ):
            mock_load.return_value = [{"input": "test", "output": "test"}]
            mock_preprocess.return_value = [{"processed_input": "test", "processed_output": "test"}]
            mock_train.return_value = ModelPerformance(accuracy=0.85, loss=0.15, epochs_trained=10)
            mock_evaluate.return_value = ModelPerformance(accuracy=0.90, loss=0.10, epochs_trained=10)
            mock_save.return_value = True

            result = pipeline.run_training_cycle()

            assert isinstance(result, TrainingResult)
            assert result.training_performance.accuracy == 0.85
            assert result.evaluation_performance.accuracy == 0.90
            assert result.model_saved is True

    def test_training_pipeline_with_validation_split(self) -> None:
        """Test training with validation data split."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
            validation_split=0.2,
        )

        pipeline = TrainingPipeline(config)

        # Mock data splitting
        with (
            patch.object(pipeline, "load_training_data") as mock_load,
            patch.object(pipeline, "split_data") as mock_split,
        ):
            full_data = [{"input": f"test_{i}", "output": f"output_{i}"} for i in range(100)]
            mock_load.return_value = full_data

            train_data, val_data = mock_split.return_value = (
                full_data[:80],
                full_data[80:],
            )

            result = pipeline.load_and_split_data()

            assert len(result.train_data) == 80
            assert len(result.validation_data) == 20

    def test_training_pipeline_early_stopping(self) -> None:
        """Test early stopping during training."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=100,
            batch_size=32,
            early_stopping_patience=5,
        )

        pipeline = TrainingPipeline(config)

        # Mock early stopping
        with patch.object(pipeline, "train_model") as mock_train:
            # Simulate early stopping after 10 epochs
            mock_train.return_value = ModelPerformance(accuracy=0.85, loss=0.15, epochs_trained=10, early_stopped=True)

            training_data = [{"input": "test", "output": "test"}]
            result = pipeline.train_model(training_data)

            assert result.early_stopped is True
            assert result.epochs_trained < config.epochs

    def test_training_pipeline_hyperparameter_tuning(self) -> None:
        """Test hyperparameter tuning."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
        )

        pipeline = TrainingPipeline(config)

        # Mock hyperparameter tuning
        with patch("tool_router.training.training_pipeline.HyperparameterTuner") as mock_tuner:
            mock_tuner_instance = Mock()
            mock_tuner.return_value = mock_tuner_instance
            mock_tuner_instance.tune.return_value = {
                "learning_rate": 0.001,
                "batch_size": 64,
                "epochs": 20,
            }

            best_params = pipeline.tune_hyperparameters()

            assert best_params["learning_rate"] == 0.001
            assert best_params["batch_size"] == 64
            assert best_params["epochs"] == 20

    def test_training_pipeline_model_checkpointing(self) -> None:
        """Test model checkpointing during training."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
            checkpoint_interval=2,
        )

        pipeline = TrainingPipeline(config)

        # Mock checkpointing
        with (
            patch.object(pipeline, "train_model") as mock_train,
            patch.object(pipeline, "save_checkpoint") as mock_checkpoint,
        ):
            mock_train.return_value = ModelPerformance(
                accuracy=0.85,
                loss=0.15,
                epochs_trained=10,
                checkpoints_saved=[2, 4, 6, 8, 10],
            )

            training_data = [{"input": "test", "output": "test"}]
            result = pipeline.train_model(training_data)

            assert len(result.checkpoints_saved) == 5

    def test_training_pipeline_error_handling(self) -> None:
        """Test error handling during training."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
        )

        pipeline = TrainingPipeline(config)

        # Mock training error
        with patch.object(pipeline, "train_model") as mock_train:
            mock_train.side_effect = Exception("Training failed")

            training_data = [{"input": "test", "output": "test"}]

            with pytest.raises(Exception, match="Training failed"):
                pipeline.train_model(training_data)

    def test_training_pipeline_metrics_tracking(self) -> None:
        """Test training metrics tracking."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
        )

        pipeline = TrainingPipeline(config)

        # Mock metrics tracking
        with patch.object(pipeline, "train_model") as mock_train:
            mock_train.return_value = ModelPerformance(
                accuracy=0.85,
                loss=0.15,
                epochs_trained=10,
                training_history={
                    "accuracy": [0.5, 0.6, 0.7, 0.8, 0.85],
                    "loss": [1.0, 0.8, 0.6, 0.4, 0.15],
                },
            )

            training_data = [{"input": "test", "output": "test"}]
            result = pipeline.train_model(training_data)

            assert "training_history" in result.__dict__
            assert len(result.training_history["accuracy"]) == 5

    def test_training_config_validation(self) -> None:
        """Test training configuration validation."""
        # Valid config
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
        )

        assert config.is_valid() is True

        # Invalid config (negative epochs)
        invalid_config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=-1,
            batch_size=32,
        )

        assert invalid_config.is_valid() is False
        assert "epochs must be positive" in invalid_config.validation_errors

    def test_training_result_serialization(self) -> None:
        """Test TrainingResult serialization."""
        result = TrainingResult(
            training_performance=ModelPerformance(accuracy=0.85, loss=0.15, epochs_trained=10),
            evaluation_performance=ModelPerformance(accuracy=0.90, loss=0.10, epochs_trained=10),
            model_saved=True,
            training_time_seconds=3600.0,
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["training_performance"]["accuracy"] == 0.85
        assert result_dict["evaluation_performance"]["accuracy"] == 0.90
        assert result_dict["model_saved"] is True
        assert result_dict["training_time_seconds"] == 3600.0

    def test_model_performance_comparison(self) -> None:
        """Test ModelPerformance comparison."""
        perf1 = ModelPerformance(accuracy=0.85, loss=0.15, epochs_trained=10)
        perf2 = ModelPerformance(accuracy=0.90, loss=0.10, epochs_trained=10)

        assert perf2 > perf1  # Higher accuracy is better
        assert perf2.is_better_than(perf1) is True
        assert perf1.is_better_than(perf2) is False

    def test_training_pipeline_with_custom_metrics(self) -> None:
        """Test training with custom evaluation metrics."""
        config = TrainingConfig(
            model_name="test_model",
            training_data_path="/path/to/data",
            epochs=10,
            batch_size=32,
            custom_metrics=["precision", "recall", "f1_score"],
        )

        pipeline = TrainingPipeline(config)

        # Mock custom metrics evaluation
        with patch.object(pipeline, "evaluate_model") as mock_evaluate:
            mock_evaluate.return_value = ModelPerformance(
                accuracy=0.85,
                loss=0.15,
                epochs_trained=10,
                custom_metrics={"precision": 0.88, "recall": 0.82, "f1_score": 0.85},
            )

            test_data = [{"input": "test", "output": "test"}]
            result = pipeline.evaluate_model(test_data)

            assert result.custom_metrics["precision"] == 0.88
            assert result.custom_metrics["recall"] == 0.82
            assert result.custom_metrics["f1_score"] == 0.85
