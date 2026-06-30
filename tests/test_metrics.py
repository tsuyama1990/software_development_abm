from abm.metrics import MetricsCollector, RunMetrics


def test_metrics_accumulation() -> None:
    collector = MetricsCollector()

    # We should add metrics per run
    metrics = RunMetrics(total_time=100.0, effort_hours=800.0, rework_time=150.0)
    collector.add_run(metrics)

    metrics2 = RunMetrics(total_time=150.0, effort_hours=900.0, rework_time=200.0)
    collector.add_run(metrics2)

    stats = collector.get_statistics()

    assert "total_time_std" in stats

def test_metrics_empty() -> None:
    collector = MetricsCollector()
    stats = collector.get_statistics()
    assert stats == {}

    # Single element to test stddev handling
    collector.add_run(RunMetrics(total_time=100.0, effort_hours=800.0, rework_time=150.0))
    stats_single = collector.get_statistics()
    assert "total_time_std" in stats_single
