#!/usr/bin/env python3

"""
Predictive Scaling System for MCP Gateway
Implements ML-based predictive scaling for optimal resource management
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
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ScalingEvent:
    """Container for scaling events"""
    timestamp: datetime
    service_name: str
    action: str  # scale_up, scale_down
    replicas_before: int
    replicas_after: int
    reason: str
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    success: bool

@dataclass
class ScalingPrediction:
    """Container for scaling predictions"""
    service_name: str
    predicted_load: float
    recommended_replicas: int
    confidence: float
    time_horizon: int  # minutes
    reasoning: str
    cost_impact: float

class PredictiveScalingEngine:
    """Predictive scaling engine using ML-based forecasting"""
    
    def __init__(self, data_dir: str = "/tmp/mcp-gateway-predictive-scaling"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Data storage
        self.scaling_history_file = self.data_dir / "scaling_history.json"
        self.models_file = self.data_dir / "scaling_models.json"
        self.predictions_file = self.data_dir / "predictions.json"
        
        # Initialize data structures
        self.scaling_history: List[ScalingEvent] = []
        self.models: Dict[str, Dict] = {}
        self.predictions: List[ScalingPrediction] = []
        
        # Scaling parameters
        self.min_history_points = 20
        self.prediction_horizon = 30  # minutes
        self.confidence_threshold = 0.7
        self.max_replicas = 5
        self.min_replicas = 1
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load historical data and models"""
        try:
            if self.scaling_history_file.exists():
                with open(self.scaling_history_file, 'r') as f:
                    data = json.load(f)
                    self.scaling_history = [
                        ScalingEvent(
                            timestamp=datetime.fromisoformat(e['timestamp']),
                            service_name=e['service_name'],
                            action=e['action'],
                            replicas_before=e['replicas_before'],
                            replicas_after=e['replicas_after'],
                            reason=e['reason'],
                            metrics_before=e['metrics_before'],
                            metrics_after=e['metrics_after'],
                            success=e['success']
                        ) for e in data
                    ]
            
            if self.models_file.exists():
                with open(self.models_file, 'r') as f:
                    self.models = json.load(f)
                    
        except Exception as e:
            logger.warning(f"Could not load data: {e}")
    
    def _save_data(self):
        """Save historical data and models"""
        try:
            # Save scaling history
            history_data = [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'service_name': e.service_name,
                    'action': e.action,
                    'replicas_before': e.replicas_before,
                    'replicas_after': e.replicas_after,
                    'reason': e.reason,
                    'metrics_before': e.metrics_before,
                    'metrics_after': e.metrics_after,
                    'success': e.success
                } for e in self.scaling_history
            ]
            
            with open(self.scaling_history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
            
            # Save models
            with open(self.models_file, 'w') as f:
                json.dump(self.models, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save data: {e}")
    
    def collect_current_metrics(self) -> Dict[str, Dict[str, float]]:
        """Collect current metrics from all services"""
        metrics = {}
        
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
                            request_rate = self._get_request_rate(service_name)
                            error_rate = self._get_error_rate(service_name)
                            
                            metrics[service_name] = {
                                'cpu_percent': cpu_percent,
                                'memory_percent': mem_percent,
                                'response_time': response_time,
                                'request_rate': request_rate,
                                'error_rate': error_rate
                            }
                            
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
    
    def _get_request_rate(self, service_name: str) -> float:
        """Get request rate for a service"""
        try:
            # Mock request rate based on service type (could be enhanced with actual metrics)
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
    
    def get_current_replicas(self, service_name: str) -> int:
        """Get current number of replicas for a service"""
        try:
            result = subprocess.run(
                ['docker-compose', '-f', 'docker-compose.production.yml', 'ps', '-q', service_name],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                return len(result.stdout.strip().split('\n'))
        except:
            pass
        
        return 1
    
    def predict_load_trend(self, service_name: str, time_horizon: int = 30) -> Dict[str, float]:
        """Predict load trend for a service"""
        # Get historical metrics for the service
        service_metrics = []
        
        # Collect recent metrics (simplified - in production would use time series database)
        for _ in range(10):  # Collect 10 data points
            metrics = self.collect_current_metrics()
            if service_name in metrics:
                service_metrics.append(metrics[service_name])
            time.sleep(1)  # Wait between collections
        
        if len(service_metrics) < 5:
            return {}
        
        # Extract time series data
        cpu_series = [m['cpu_percent'] for m in service_metrics]
        memory_series = [m['memory_percent'] for m in service_metrics]
        response_series = [m['response_time'] for m in service_metrics]
        request_series = [m['request_rate'] for m in service_metrics]
        
        # Simple linear prediction (could be enhanced with more sophisticated ML models)
        def predict_series(series, horizon):
            if len(series) < 2:
                return series[-1] if series else 0.0
            
            # Calculate trend
            n = len(series)
            x = list(range(n))
            
            x_mean = statistics.mean(x)
            y_mean = statistics.mean(series)
            
            numerator = sum((x[i] - x_mean) * (series[i] - y_mean) for i in range(n))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return y_mean
            
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean
            
            # Predict future value
            future_x = n + horizon
            return intercept + slope * future_x
        
        predicted_cpu = predict_series(cpu_series, time_horizon)
        predicted_memory = predict_series(memory_series, time_horizon)
        predicted_response = predict_series(response_series, time_horizon)
        predicted_requests = predict_series(request_series, time_horizon)
        
        # Calculate prediction confidence
        confidence = self._calculate_prediction_confidence(service_metrics)
        
        return {
            'predicted_cpu': max(0, min(100, predicted_cpu)),
            'predicted_memory': max(0, min(100, predicted_memory)),
            'predicted_response': max(0, predicted_response),
            'predicted_requests': max(0, predicted_requests),
            'confidence': confidence
        }
    
    def _calculate_prediction_confidence(self, metrics: List[Dict[str, float]]) -> float:
        """Calculate confidence in predictions"""
        if len(metrics) < 5:
            return 0.3  # Low confidence with little data
        
        # Calculate variance in metrics
        cpu_variance = statistics.variance([m['cpu_percent'] for m in metrics]) if len(metrics) > 1 else 0
        memory_variance = statistics.variance([m['memory_percent'] for m in metrics]) if len(metrics) > 1 else 0
        response_variance = statistics.variance([m['response_time'] for m in metrics]) if len(metrics) > 1 else 0
        
        # Lower variance = higher confidence
        avg_variance = (cpu_variance + memory_variance + response_variance) / 3
        confidence = max(0.3, 1.0 - (avg_variance / 1000))  # Normalize
        
        return min(1.0, confidence)
    
    def calculate_optimal_replicas(self, service_name: str, predicted_load: Dict[str, float]) -> int:
        """Calculate optimal number of replicas based on predicted load"""
        if not predicted_load:
            return 1
        
        # Base calculation on CPU and memory usage
        cpu_load = predicted_load['predicted_cpu']
        memory_load = predicted_load['predicted_memory']
        response_time = predicted_load['predicted_response']
        request_rate = predicted_load['predicted_requests']
        
        # Service-specific scaling factors
        scaling_factors = {
            'gateway': {'cpu_weight': 0.4, 'memory_weight': 0.3, 'response_weight': 0.3},
            'service-manager': {'cpu_weight': 0.5, 'memory_weight': 0.4, 'response_weight': 0.1},
            'web-admin': {'cpu_weight': 0.3, 'memory_weight': 0.4, 'response_weight': 0.3},
            'postgres': {'cpu_weight': 0.3, 'memory_weight': 0.6, 'response_weight': 0.1},
            'redis': {'cpu_weight': 0.4, 'memory_weight': 0.5, 'response_weight': 0.1}
        }
        
        factors = scaling_factors.get(service_name, scaling_factors['gateway'])
        
        # Calculate load score
        load_score = (
            cpu_load * factors['cpu_weight'] +
            memory_load * factors['memory_weight'] +
            min(response_time / 1000, 100) * factors['response_weight']  # Normalize response time
        )
        
        # Calculate replicas based on load score
        if load_score < 30:
            replicas = 1
        elif load_score < 50:
            replicas = 2
        elif load_score < 70:
            replicas = 3
        elif load_score < 85:
            replicas = 4
        else:
            replicas = 5
        
        # Consider request rate for high-traffic services
        if request_rate > 200 and service_name == 'gateway':
            replicas = min(self.max_replicas, replicas + 1)
        
        return max(self.min_replicas, min(self.max_replicas, replicas))
    
    def generate_scaling_predictions(self) -> List[ScalingPrediction]:
        """Generate scaling predictions for all services"""
        predictions = []
        
        # Get current metrics
        current_metrics = self.collect_current_metrics()
        
        for service_name in current_metrics.keys():
            # Predict load trend
            predicted_load = self.predict_load_trend(service_name, self.prediction_horizon)
            
            if predicted_load and predicted_load['confidence'] > self.confidence_threshold:
                # Calculate optimal replicas
                optimal_replicas = self.calculate_optimal_replicas(service_name, predicted_load)
                current_replicas = self.get_current_replicas(service_name)
                
                # Determine if scaling is needed
                action_needed = optimal_replicas != current_replicas
                confidence = predicted_load['confidence']
                
                # Calculate cost impact
                cost_impact = self._calculate_cost_impact(current_replicas, optimal_replicas)
                
                # Generate reasoning
                reasoning = self._generate_scaling_reasoning(
                    current_metrics[service_name],
                    predicted_load,
                    current_replicas,
                    optimal_replicas
                )
                
                prediction = ScalingPrediction(
                    service_name=service_name,
                    predicted_load=predicted_load['predicted_cpu'],  # Use CPU as primary load indicator
                    recommended_replicas=optimal_replicas,
                    confidence=confidence,
                    time_horizon=self.prediction_horizon,
                    reasoning=reasoning,
                    cost_impact=cost_impact
                )
                
                predictions.append(prediction)
        
        return predictions
    
    def _calculate_cost_impact(self, current_replicas: int, recommended_replicas: int) -> float:
        """Calculate cost impact of scaling change"""
        # Simplified cost calculation (could be enhanced with actual cost data)
        replica_cost = 0.1  # Cost per replica per hour (arbitrary units)
        
        current_cost = current_replicas * replica_cost
        recommended_cost = recommended_replicas * replica_cost
        
        return recommended_cost - current_cost
    
    def _generate_scaling_reasoning(self, current_metrics: Dict[str, float], 
                                  predicted_load: Dict[str, float], 
                                  current_replicas: int, 
                                  optimal_replicas: int) -> str:
        """Generate reasoning for scaling recommendation"""
        reasons = []
        
        if predicted_load['predicted_cpu'] > 80:
            reasons.append(f"High CPU predicted ({predicted_load['predicted_cpu']:.1f}%)")
        
        if predicted_load['predicted_memory'] > 85:
            reasons.append(f"High memory predicted ({predicted_load['predicted_memory']:.1f}%)")
        
        if predicted_load['predicted_response'] > 2000:
            reasons.append(f"High response time predicted ({predicted_load['predicted_response']:.1f}ms)")
        
        if optimal_replicas > current_replicas:
            reasons.append(f"Scale up recommended ({current_replicas} → {optimal_replicas})")
        elif optimal_replicas < current_replicas:
            reasons.append(f"Scale down recommended ({current_replicas} → {optimal_replicas})")
        
        if not reasons:
            reasons.append("Optimal configuration maintained")
        
        return "; ".join(reasons)
    
    def apply_scaling_decision(self, prediction: ScalingPrediction) -> bool:
        """Apply a scaling decision based on prediction"""
        logger.info(f"Applying scaling decision for {prediction.service_name}")
        
        try:
            current_replicas = self.get_current_replicas(prediction.service_name)
            
            if prediction.recommended_replicas != current_replicas:
                # Perform scaling
                success = self._scale_service(prediction.service_name, prediction.recommended_replicas)
                
                if success:
                    # Record scaling event
                    current_metrics = self.collect_current_metrics()
                    metrics_before = current_metrics.get(prediction.service_name, {})
                    
                    # Wait briefly for scaling to take effect
                    time.sleep(5)
                    
                    # Get metrics after scaling
                    metrics_after = self.collect_current_metrics().get(prediction.service_name, {})
                    
                    scaling_event = ScalingEvent(
                        timestamp=datetime.now(),
                        service_name=prediction.service_name,
                        action="scale_up" if prediction.recommended_replicas > current_replicas else "scale_down",
                        replicas_before=current_replicas,
                        replicas_after=prediction.recommended_replicas,
                        reason=prediction.reasoning,
                        metrics_before=metrics_before,
                        metrics_after=metrics_after,
                        success=True
                    )
                    
                    self.scaling_history.append(scaling_event)
                    logger.info(f"Successfully scaled {prediction.service_name} to {prediction.recommended_replicas} replicas")
                    return True
                else:
                    logger.error(f"Failed to scale {prediction.service_name}")
                    return False
            else:
                logger.info(f"No scaling needed for {prediction.service_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to apply scaling decision: {e}")
            return False
    
    def _scale_service(self, service_name: str, replicas: int) -> bool:
        """Scale a service to specified number of replicas"""
        try:
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose.production.yml',
                'up', '-d', '--scale', f'{service_name}={replicas}'
            ], capture_output=True, text=True, timeout=60)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to scale {service_name}: {e}")
            return False
    
    def run_predictive_scaling_cycle(self) -> Dict[str, any]:
        """Run a complete predictive scaling cycle"""
        logger.info("Starting predictive scaling cycle")
        
        # Generate predictions
        predictions = self.generate_scaling_predictions()
        
        # Apply scaling decisions
        applied_predictions = []
        for prediction in predictions:
            if prediction.confidence > self.confidence_threshold:
                if self.apply_scaling_decision(prediction):
                    applied_predictions.append(prediction)
        
        # Save data
        self._save_data()
        
        # Generate summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'predictions_generated': len(predictions),
            'predictions_applied': len(applied_predictions),
            'confidence_threshold': self.confidence_threshold,
            'predictions': [
                {
                    'service_name': p.service_name,
                    'recommended_replicas': p.recommended_replicas,
                    'confidence': p.confidence,
                    'reasoning': p.reasoning,
                    'cost_impact': p.cost_impact
                } for p in predictions
            ]
        }
        
        return summary
    
    def get_scaling_report(self) -> Dict[str, any]:
        """Get a comprehensive scaling report"""
        services = list(set(e.service_name for e in self.scaling_history))
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_scaling_events': len(self.scaling_history),
            'services_analyzed': len(services),
            'scaling_history': {},
            'current_metrics': self.collect_current_metrics()
        }
        
        for service in services:
            service_events = [e for e in self.scaling_history if e.service_name == service]
            
            if service_events:
                success_rate = sum(1 for e in service_events if e.success) / len(service_events)
                avg_confidence = 0.0  # Could be calculated from predictions
                
                report['scaling_history'][service] = {
                    'total_events': len(service_events),
                    'success_rate': success_rate,
                    'last_event': service_events[-1].timestamp.isoformat(),
                    'last_action': service_events[-1].action,
                    'current_replicas': self.get_current_replicas(service)
                }
        
        return report

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Predictive Scaling for MCP Gateway')
    parser.add_argument('--predict', action='store_true', help='Generate scaling predictions')
    parser.add_argument('--scale', action='store_true', help='Apply predictive scaling')
    parser.add_argument('--report', action='store_true', help='Generate scaling report')
    parser.add_argument('--service', help='Specific service to analyze')
    parser.add_argument('--horizon', type=int, default=30, help='Prediction horizon in minutes')
    parser.add_argument('--confidence', type=float, default=0.7, help='Confidence threshold')
    
    args = parser.parse_args()
    
    scaler = PredictiveScalingEngine()
    scaler.prediction_horizon = args.horizon
    scaler.confidence_threshold = args.confidence
    
    if args.predict:
        if args.service:
            predicted_load = scaler.predict_load_trend(args.service, args.horizon)
            optimal_replicas = scaler.calculate_optimal_replicas(args.service, predicted_load)
            print(f"Prediction for {args.service}:")
            print(f"Predicted load: {predicted_load}")
            print(f"Optimal replicas: {optimal_replicas}")
        else:
            predictions = scaler.generate_scaling_predictions()
            print(f"Generated {len(predictions)} predictions")
            for pred in predictions:
                print(f"- {pred.service_name}: {pred.recommended_replicas} replicas (confidence: {pred.confidence:.2f})")
                
    elif args.scale:
        summary = scaler.run_predictive_scaling_cycle()
        print(f"Predictive scaling cycle completed:")
        print(f"- Predictions generated: {summary['predictions_generated']}")
        print(f"- Predictions applied: {summary['predictions_applied']}")
        
    elif args.report:
        report = scaler.get_scaling_report()
        print(json.dumps(report, indent=2))
        
    else:
        # Default: run predictive scaling cycle
        summary = scaler.run_predictive_scaling_cycle()
        print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()