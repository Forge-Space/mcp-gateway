#!/usr/bin/env python3

"""
ML-Based Monitoring System for MCP Gateway
Implements machine learning-based anomaly detection and monitoring
"""

import json
import time
import statistics
import subprocess
import sys
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging
from collections import defaultdict, deque
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MonitoringMetric:
    """Container for monitoring metrics"""
    timestamp: datetime
    service_name: str
    cpu_percent: float
    memory_percent: float
    response_time: float
    error_rate: float
    request_rate: float
    disk_usage: float
    network_io: float

@dataclass
class AnomalyDetection:
    """Container for anomaly detection results"""
    timestamp: datetime
    service_name: str
    anomaly_type: str
    severity: str  # low, medium, high, critical
    confidence: float
    metrics: Dict[str, float]
    baseline: Dict[str, float]
    deviation: Dict[str, float]
    description: str

class MLMonitoringEngine:
    """ML-based monitoring engine with anomaly detection"""

    def __init__(self, data_dir: str = "/tmp/mcp-gateway-ml-monitoring"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Data storage
        self.metrics_file = self.data_dir / "metrics.json"
        self.models_file = self.data_dir / "ml_models.pkl"
        self.anomalies_file = self.data_dir / "anomalies.json"
        self.baselines_file = self.data_dir / "baselines.json"

        # Initialize data structures
        self.metrics_history: List[MonitoringMetric] = []
        self.anomalies: List[AnomalyDetection] = []
        self.baselines: Dict[str, Dict[str, float]] = {}

        # ML models
        self.anomaly_detectors: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}

        # Monitoring parameters
        self.min_training_samples = 100
        self.anomaly_threshold = 0.1
        self.baseline_window = 1000  # Number of samples for baseline
        self.detection_window = 50   # Recent samples for detection

        # Load existing data
        self._load_data()

        # Initialize models
        self._initialize_models()

    def _load_data(self):
        """Load historical data and models"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    self.metrics_history = [
                        MonitoringMetric(
                            timestamp=datetime.fromisoformat(m['timestamp']),
                            service_name=m['service_name'],
                            cpu_percent=m['cpu_percent'],
                            memory_percent=m['memory_percent'],
                            response_time=m['response_time'],
                            error_rate=m['error_rate'],
                            request_rate=m['request_rate'],
                            disk_usage=m['disk_usage'],
                            network_io=m['network_io']
                        ) for m in data
                    ]

            if self.models_file.exists():
                with open(self.models_file, 'rb') as f:
                    models_data = pickle.load(f)
                    self.anomaly_detectors = models_data.get('detectors', {})
                    self.scalers = models_data.get('scalers', {})

            if self.baselines_file.exists():
                with open(self.baselines_file, 'r') as f:
                    self.baselines = json.load(f)

        except Exception as e:
            logger.warning(f"Could not load data: {e}")

    def _save_data(self):
        """Save historical data and models"""
        try:
            # Save metrics
            metrics_data = [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'service_name': m.service_name,
                    'cpu_percent': m.cpu_percent,
                    'memory_percent': m.memory_percent,
                    'response_time': m.response_time,
                    'error_rate': m.error_rate,
                    'request_rate': m.request_rate,
                    'disk_usage': m.disk_usage,
                    'network_io': m.network_io
                } for m in self.metrics_history
            ]

            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)

            # Save ML models
            models_data = {
                'detectors': self.anomaly_detectors,
                'scalers': self.scalers
            }

            with open(self.models_file, 'wb') as f:
                pickle.dump(models_data, f)

            # Save baselines
            with open(self.baselines_file, 'w') as f:
                json.dump(self.baselines, f, indent=2)

        except Exception as e:
            logger.error(f"Could not save data: {e}")

    def _initialize_models(self):
        """Initialize ML models for anomaly detection"""
        services = ['gateway', 'service-manager', 'postgres', 'redis', 'web-admin']

        for service in services:
            # Initialize anomaly detector
            self.anomaly_detectors[service] = IsolationForest(
                n_estimators=100,
                contamination='auto',
                random_state=42
            )

            # Initialize scaler
            self.scalers[service] = StandardScaler()

    def collect_metrics(self) -> List[MonitoringMetric]:
        """Collect current metrics from all services"""
        metrics = []

        try:
            # Get Docker stats
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format',
                 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}'],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header

                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            container_name = parts[0].strip()
                            cpu_percent = float(parts[1].rstrip('%'))
                            mem_percent = float(parts[3].rstrip('%'))

                            # Extract service name
                            service_name = container_name.replace('forge-', '').replace('-prod', '')

                            # Get additional metrics
                            response_time = self._get_response_time(service_name)
                            error_rate = self._get_error_rate(service_name)
                            request_rate = self._get_request_rate(service_name)
                            disk_usage = self._get_disk_usage()
                            network_io = self._get_network_io()

                            metric = MonitoringMetric(
                                timestamp=datetime.now(),
                                service_name=service_name,
                                cpu_percent=cpu_percent,
                                memory_percent=mem_percent,
                                response_time=response_time,
                                error_rate=error_rate,
                                request_rate=request_rate,
                                disk_usage=disk_usage,
                                network_io=network_io
                            )

                            metrics.append(metric)

        except Exception as e:
            logger.error(f"Could not collect metrics: {e}")

        return metrics

    def _get_response_time(self, service_name: str) -> float:
        """Get response time for a service"""
        try:
            if service_name == "gateway":
                result = subprocess.run(
                    ['curl', '-o', '/dev/null', '-s', '-w', '%{time_total}',
                     'http://localhost:8000/health'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return float(result.stdout.strip()) * 1000
            elif service_name == "service-manager":
                result = subprocess.run(
                    ['curl', '-o', '/dev/null', '-s', '-w', '%{time_total}',
                     'http://localhost:9000/health'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    return float(result.stdout.strip()) * 1000
        except:
            pass

        return 0.0

    def _get_error_rate(self, service_name: str) -> float:
        """Get error rate for a service"""
        try:
            result = subprocess.run(
                ['docker', 'logs', '--since=5m', f'forge-{service_name}-prod'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                lines = result.stdout.split('\n')
                error_count = sum(1 for line in lines if 'error' in line.lower() or 'failed' in line.lower())
                total_count = len(lines)

                if total_count > 0:
                    return (error_count / total_count) * 100
        except:
            pass

        return 0.0

    def _get_request_rate(self, service_name: str) -> float:
        """Get request rate for a service"""
        try:
            # Mock request rate based on service type
            if service_name == "gateway":
                return 100.0  # requests per minute
            elif service_name == "service-manager":
                return 50.0
            elif service_name == "web-admin":
                return 30.0
            else:
                return 20.0
        except:
            pass

        return 0.0

    def _get_disk_usage(self) -> float:
        """Get disk usage percentage"""
        try:
            result = subprocess.run(['df', '/'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if line.startswith('/dev/'):
                        usage = line.split()[4].rstrip('%')
                        return float(usage)
        except:
            pass

        return 0.0

    def _get_network_io(self) -> float:
        """Get network I/O (mock implementation)"""
        try:
            # Mock network I/O (could be enhanced with actual network stats)
            return 10.0  # MB/s
        except:
            pass

        return 0.0

    def update_baselines(self):
        """Update baseline metrics for all services"""
        services = list(set(m.service_name for m in self.metrics_history))

        for service in services:
            service_metrics = [m for m in self.metrics_history if m.service_name == service]

            if len(service_metrics) >= self.baseline_window:
                # Calculate baseline as rolling average
                recent_metrics = service_metrics[-self.baseline_window:]

                self.baselines[service] = {
                    'cpu_percent': statistics.mean([m.cpu_percent for m in recent_metrics]),
                    'memory_percent': statistics.mean([m.memory_percent for m in recent_metrics]),
                    'response_time': statistics.mean([m.response_time for m in recent_metrics]),
                    'error_rate': statistics.mean([m.error_rate for m in recent_metrics]),
                    'request_rate': statistics.mean([m.request_rate for m in recent_metrics]),
                    'disk_usage': statistics.mean([m.disk_usage for m in recent_metrics]),
                    'network_io': statistics.mean([m.network_io for m in recent_metrics])
                }

                logger.info(f"Updated baseline for {service}")

    def train_anomaly_detectors(self):
        """Train anomaly detection models"""
        services = list(set(m.service_name for m in self.metrics_history))

        for service in services:
            service_metrics = [m for m in self.metrics_history if m.service_name == service]

            if len(service_metrics) >= self.min_training_samples:
                # Prepare training data
                features = []
                for m in service_metrics:
                    features.append([
                        m.cpu_percent,
                        m.memory_percent,
                        m.response_time,
                        m.error_rate,
                        m.request_rate,
                        m.disk_usage,
                        m.network_io
                    ])

                # Scale features
                if service in self.scalers:
                    try:
                        scaled_features = self.scalers[service].fit_transform(features)

                        # Train anomaly detector
                        self.anomaly_detectors[service].fit(scaled_features)

                        logger.info(f"Trained anomaly detector for {service} with {len(features)} samples")
                    except Exception as e:
                        logger.error(f"Failed to train anomaly detector for {service}: {e}")

    def detect_anomalies(self) -> List[AnomalyDetection]:
        """Detect anomalies in current metrics"""
        anomalies = []

        current_metrics = self.collect_metrics()

        for metric in current_metrics:
            if metric.service_name in self.anomaly_detectors and metric.service_name in self.scalers:
                try:
                    # Prepare features
                    features = [[
                        metric.cpu_percent,
                        metric.memory_percent,
                        metric.response_time,
                        metric.error_rate,
                        metric.request_rate,
                        metric.disk_usage,
                        metric.network_io
                    ]]

                    # Scale features
                    scaled_features = self.scalers[metric.service_name].transform(features)

                    # Predict anomaly score
                    anomaly_score = self.anomaly_detectors[metric.service_name].decision_function(scaled_features)[0]

                    if anomaly_score < -self.anomaly_threshold:  # Isolation Forest: negative = anomaly
                        # Calculate deviation from baseline
                        baseline = self.baselines.get(metric.service_name, {})
                        deviation = {}

                        if baseline:
                            deviation['cpu_percent'] = metric.cpu_percent - baseline.get('cpu_percent', 0)
                            deviation['memory_percent'] = metric.memory_percent - baseline.get('memory_percent', 0)
                            deviation['response_time'] = metric.response_time - baseline.get('response_time', 0)
                            deviation['error_rate'] = metric.error_rate - baseline.get('error_rate', 0)
                            deviation['request_rate'] = metric.request_rate - baseline.get('request_rate', 0)

                        # Determine anomaly type and severity
                        anomaly_type, severity = self._classify_anomaly(metric, deviation)

                        # Calculate confidence
                        confidence = min(1.0, abs(anomaly_score))

                        anomaly = AnomalyDetection(
                            timestamp=datetime.now(),
                            service_name=metric.service_name,
                            anomaly_type=anomaly_type,
                            severity=severity,
                            confidence=confidence,
                            metrics={
                                'cpu_percent': metric.cpu_percent,
                                'memory_percent': metric.memory_percent,
                                'response_time': metric.response_time,
                                'error_rate': metric.error_rate,
                                'request_rate': metric.request_rate,
                                'disk_usage': metric.disk_usage,
                                'network_io': metric.network_io
                            },
                            baseline=baseline,
                            deviation=deviation,
                            description=self._generate_anomaly_description(metric, deviation, anomaly_type)
                        )

                        anomalies.append(anomaly)

                except Exception as e:
                    logger.error(f"Failed to detect anomaly for {metric.service_name}: {e}")

        return anomalies

    def _classify_anomaly(self, metric: MonitoringMetric, deviation: Dict[str, float]) -> Tuple[str, str]:
        """Classify anomaly type and severity"""
        # Determine primary anomaly type based on largest deviation
        max_deviation = 0
        primary_metric = 'cpu_percent'

        for metric_name, dev_value in deviation.items():
            if abs(dev_value) > abs(max_deviation):
                max_deviation = dev_value
                primary_metric = metric_name

        # Classify anomaly type
        if primary_metric == 'error_rate':
            anomaly_type = 'error_spike'
        elif primary_metric == 'response_time':
            anomaly_type = 'performance_degradation'
        elif primary_metric == 'cpu_percent':
            anomaly_type = 'resource_exhaustion'
        elif primary_metric == 'memory_percent':
            anomaly_type = 'memory_pressure'
        elif primary_metric == 'disk_usage':
            anomaly_type = 'storage_exhaustion'
        else:
            anomaly_type = 'unknown'

        # Determine severity based on deviation magnitude
        if abs(max_deviation) > 50:
            severity = 'critical'
        elif abs(max_deviation) > 25:
            severity = 'high'
        elif abs(max_deviation) > 10:
            severity = 'medium'
        else:
            severity = 'low'

        return anomaly_type, severity

    def _generate_anomaly_description(self, metric: MonitoringMetric,
                                     deviation: Dict[str, float],
                                     anomaly_type: str) -> str:
        """Generate human-readable anomaly description"""
        descriptions = []

        if anomaly_type == 'error_spike':
            descriptions.append(f"Error rate spike detected")
            if deviation.get('error_rate', 0) > 0:
                descriptions.append(f"Error rate increased by {abs(deviation['error_rate']):.1f}%")
        elif anomaly_type == 'performance_degradation':
            descriptions.append("Performance degradation detected")
            if deviation.get('response_time', 0) > 0:
                descriptions.append(f"Response time increased by {abs(deviation['response_time']):.1f}ms")
        elif anomaly_type == 'resource_exhaustion':
            descriptions.append("Resource exhaustion detected")
            if deviation.get('cpu_percent', 0) > 0:
                descriptions.append(f"CPU usage increased by {abs(deviation['cpu_percent']):.1f}%")
        elif anomaly_type == 'memory_pressure':
            descriptions.append("Memory pressure detected")
            if deviation.get('memory_percent', 0) > 0:
                descriptions.append(f"Memory usage increased by {abs(deviation['memory_percent']):.1f}%")
        elif anomaly_type == 'storage_exhaustion':
            descriptions.append("Storage exhaustion detected")
            if deviation.get('disk_usage', 0) > 0:
                descriptions.append(f"Disk usage increased by {abs(deviation['disk_usage']):.1f}%")

        if not descriptions:
            descriptions.append("Unusual behavior detected")

        return "; ".join(descriptions)

    def run_monitoring_cycle(self) -> Dict[str, any]:
        """Run a complete ML-based monitoring cycle"""
        logger.info("Starting ML-based monitoring cycle")

        # Collect current metrics
        current_metrics = self.collect_metrics()
        self.metrics_history.extend(current_metrics)

        # Keep only recent data (last 5000 data points)
        if len(self.metrics_history) > 5000:
            self.metrics_history = self.metrics_history[-5000:]

        # Update baselines periodically
        if len(self.metrics_history) % 100 == 0:
            self.update_baselines()

        # Train models periodically
        if len(self.metrics_history) % 500 == 0:
            self.train_anomaly_detectors()

        # Detect anomalies
        anomalies = self.detect_anomalies()
        self.anomalies.extend(anomalies)

        # Keep only recent anomalies (last 1000)
        if len(self.anomalies) > 1000:
            self.anomalies = self.anomalies[-1000:]

        # Save data
        self._save_data()

        # Generate summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'metrics_collected': len(current_metrics),
            'total_metrics': len(self.metrics_history),
            'anomalies_detected': len(anomalies),
            'anomaly_types': list(set(a.anomaly_type for a in anomalies)),
            'severity_distribution': {
                'critical': len([a for a in anomalies if a.severity == 'critical']),
                'high': len([a for a in anomalies if a.severity == 'high']),
                'medium': len([a for a in anomalies if a.severity == 'medium']),
                'low': len([a for a in anomalies if a.severity == 'low'])
            },
            'anomalies': [
                {
                    'service_name': a.service_name,
                    'anomaly_type': a.anomaly_type,
                    'severity': a.severity,
                    'confidence': a.confidence,
                    'description': a.description,
                    'timestamp': a.timestamp.isoformat()
                } for a in anomalies
            ]
        }

        return summary

    def get_monitoring_report(self) -> Dict[str, any]:
        """Get a comprehensive monitoring report"""
        services = list(set(m.service_name for m in self.metrics_history))

        report = {
            'timestamp': datetime.now().isoformat(),
            'total_metrics': len(self.metrics_history),
            'services_monitored': len(services),
            'total_anomalies': len(self.anomalies),
            'models_trained': len(self.anomaly_detectors),
            'baselines_established': len(self.baselines),
            'service_analysis': {},
            'recent_anomalies': [
                {
                    'service_name': a.service_name,
                    'anomaly_type': a.anomaly_type,
                    'severity': a.severity,
                    'confidence': a.confidence,
                    'description': a.description,
                    'timestamp': a.timestamp.isoformat()
                } for a in self.anomalies[-10:]  # Last 10 anomalies
            ]
        }

        for service in services:
            service_metrics = [m for m in self.metrics_history if m.service_name == service]

            if service_metrics:
                report['service_analysis'][service] = {
                    'total_metrics': len(service_metrics),
                    'avg_cpu': statistics.mean([m.cpu_percent for m in service_metrics]),
                    'avg_memory': statistics.mean([m.memory_percent for m in service_metrics]),
                    'avg_response': statistics.mean([m.response_time for m in service_metrics]),
                    'avg_error_rate': statistics.mean([m.error_rate for m in service_metrics]),
                    'avg_request_rate': statistics.mean([m.request_rate for m in service_metrics]),
                    'baseline': self.baselines.get(service, {}),
                    'anomaly_count': len([a for a in self.anomalies if a.service_name == service])
                }

        return report

def main():
    """Main function for CLI usage"""
    import argparse

    parser = argparse.ArgumentParser(description='ML-Based Monitoring for MCP Gateway')
    parser.add_argument('--monitor', action='store_true', help='Run monitoring cycle')
    parser.add_argument('--train', action='store_true', help='Train anomaly detection models')
    parser.add_argument('--detect', action='store_true', help='Detect anomalies')
    parser.add_argument('--report', action='store_true', help='Generate monitoring report')
    parser.add_argument('--service', help='Specific service to monitor')
    parser.add_argument('--threshold', type=float, default=0.1, help='Anomaly threshold')

    args = parser.parse_args()

    monitor = MLMonitoringEngine()
    monitor.anomaly_threshold = args.threshold

    if args.train:
        monitor.train_anomaly_detectors()
        print(f"Trained anomaly detection models")

    elif args.detect:
        anomalies = monitor.detect_anomalies()
        print(f"Detected {len(anomalies)} anomalies")
        for anomaly in anomalies:
            print(f"- {anomaly.service_name}: {anomaly.anomaly_type} ({anomaly.severity})")

    elif args.report:
        report = monitor.get_monitoring_report()
        print(json.dumps(report, indent=2))

    elif args.monitor:
        summary = monitor.run_monitoring_cycle()
        print(json.dumps(summary, indent=2))

    else:
        # Default: run monitoring cycle
        summary = monitor.run_monitoring_cycle()
        print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
