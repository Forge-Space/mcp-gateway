#!/usr/bin/env python3

"""
AI-Driven Optimization System for MCP Gateway
Implements machine learning-based optimization for performance and resource management
"""

import json
import time
import statistics
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MetricData:
    """Container for metric data"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    response_time: float
    error_rate: float
    request_count: int
    service_name: str

@dataclass
class OptimizationRecommendation:
    """Container for optimization recommendations"""
    action: str
    target_service: str
    confidence: float
    expected_improvement: float
    reasoning: str
    priority: str  # high, medium, low

class AIOptimizationEngine:
    """AI-driven optimization engine for MCP Gateway"""
    
    def __init__(self, data_dir: str = "/tmp/mcp-gateway-ai-optimization"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Historical data storage
        self.metrics_file = self.data_dir / "metrics.json"
        self.models_file = self.data_dir / "models.json"
        self.recommendations_file = self.data_dir / "recommendations.json"
        
        # Initialize data structures
        self.metrics_history: List[MetricData] = []
        self.models: Dict[str, Dict] = {}
        self.recommendations: List[OptimizationRecommendation] = []
        
        # Optimization parameters
        self.min_data_points = 50
        self.optimization_interval = 300  # 5 minutes
        self.confidence_threshold = 0.7
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load historical data and models"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    self.metrics_history = [
                        MetricData(
                            timestamp=datetime.fromisoformat(m['timestamp']),
                            cpu_percent=m['cpu_percent'],
                            memory_percent=m['memory_percent'],
                            response_time=m['response_time'],
                            error_rate=m['error_rate'],
                            request_count=m['request_count'],
                            service_name=m['service_name']
                        ) for m in data
                    ]
            
            if self.models_file.exists():
                with open(self.models_file, 'r') as f:
                    self.models = json.load(f)
                    
        except Exception as e:
            logger.warning(f"Could not load data: {e}")
    
    def _save_data(self):
        """Save historical data and models"""
        try:
            # Save metrics
            metrics_data = [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'cpu_percent': m.cpu_percent,
                    'memory_percent': m.memory_percent,
                    'response_time': m.response_time,
                    'error_rate': m.error_rate,
                    'request_count': m.request_count,
                    'service_name': m.service_name
                } for m in self.metrics_history
            ]
            
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            # Save models
            with open(self.models_file, 'w') as f:
                json.dump(self.models, f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save data: {e}")
    
    def collect_metrics(self) -> List[MetricData]:
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
                            mem_usage = parts[2]
                            mem_percent = float(parts[3].rstrip('%'))
                            
                            # Extract service name from container name
                            service_name = container_name.replace('forge-', '').replace('-prod', '')
                            
                            # Get response time and error rate (mock for now)
                            response_time = self._get_response_time(service_name)
                            error_rate = self._get_error_rate(service_name)
                            request_count = self._get_request_count(service_name)
                            
                            metric = MetricData(
                                timestamp=datetime.now(),
                                cpu_percent=cpu_percent,
                                memory_percent=mem_percent,
                                response_time=response_time,
                                error_rate=error_rate,
                                request_count=request_count,
                                service_name=service_name
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
                    return float(result.stdout.strip()) * 1000  # Convert to ms
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
        
        return 0.0  # Default if unavailable
    
    def _get_error_rate(self, service_name: str) -> float:
        """Get error rate for a service"""
        try:
            # Check recent logs for errors (simplified)
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
        
        return 0.0  # Default if unavailable
    
    def _get_request_count(self, service_name: str) -> int:
        """Get request count for a service"""
        try:
            # Mock request count based on service type
            if service_name == "gateway":
                return 100  # Gateway handles most requests
            elif service_name == "service-manager":
                return 50   # Service manager handles fewer requests
            else:
                return 25   # Other services
        except:
            pass
        
        return 0
    
    def analyze_performance_trends(self, service_name: str) -> Dict[str, float]:
        """Analyze performance trends for a specific service"""
        service_metrics = [m for m in self.metrics_history if m.service_name == service_name]
        
        if len(service_metrics) < self.min_data_points:
            return {}
        
        # Calculate trends
        cpu_trend = self._calculate_trend([m.cpu_percent for m in service_metrics])
        memory_trend = self._calculate_trend([m.memory_percent for m in service_metrics])
        response_trend = self._calculate_trend([m.response_time for m in service_metrics])
        error_trend = self._calculate_trend([m.error_rate for m in service_metrics])
        
        # Calculate averages
        avg_cpu = statistics.mean([m.cpu_percent for m in service_metrics])
        avg_memory = statistics.mean([m.memory_percent for m in service_metrics])
        avg_response = statistics.mean([m.response_time for m in service_metrics])
        avg_error = statistics.mean([m.error_rate for m in service_metrics])
        
        return {
            'cpu_trend': cpu_trend,
            'memory_trend': memory_trend,
            'response_trend': response_trend,
            'error_trend': error_trend,
            'avg_cpu': avg_cpu,
            'avg_memory': avg_memory,
            'avg_response': avg_response,
            'avg_error': avg_error
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend (positive = increasing, negative = decreasing)"""
        if len(values) < 2:
            return 0.0
        
        # Simple linear regression to calculate trend
        n = len(values)
        x = list(range(n))
        
        # Calculate slope
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope
    
    def predict_resource_needs(self, service_name: str, time_horizon: int = 60) -> Dict[str, float]:
        """Predict resource needs for a service"""
        trends = self.analyze_performance_trends(service_name)
        
        if not trends:
            return {}
        
        # Predict future values based on trends
        future_cpu = trends['avg_cpu'] + (trends['cpu_trend'] * time_horizon)
        future_memory = trends['avg_memory'] + (trends['memory_trend'] * time_horizon)
        future_response = trends['avg_response'] + (trends['response_trend'] * time_horizon)
        
        return {
            'predicted_cpu': max(0, min(100, future_cpu)),
            'predicted_memory': max(0, min(100, future_memory)),
            'predicted_response': max(0, future_response),
            'confidence': self._calculate_prediction_confidence(trends)
        }
    
    def _calculate_prediction_confidence(self, trends: Dict[str, float]) -> float:
        """Calculate confidence in predictions"""
        if not trends:
            return 0.0
        
        # Base confidence on data availability and trend stability
        service_metrics = [m for m in self.metrics_history if m.service_name == trends.get('service_name', '')]
        data_confidence = min(1.0, len(service_metrics) / 100)  # More data = higher confidence
        
        # Adjust confidence based on trend volatility
        trend_values = [trends['cpu_trend'], trends['memory_trend'], trends['response_trend']]
        trend_volatility = statistics.stdev(trend_values) if len(trend_values) > 1 else 0
        stability_confidence = max(0.0, 1.0 - (trend_volatility / 10))  # Less volatile = higher confidence
        
        return (data_confidence + stability_confidence) / 2
    
    def generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on analysis"""
        recommendations = []
        
        # Analyze each service
        services = list(set(m.service_name for m in self.metrics_history))
        
        for service in services:
            trends = self.analyze_performance_trends(service)
            predictions = self.predict_resource_needs(service)
            
            if not trends:
                continue
            
            # High CPU usage recommendation
            if trends['avg_cpu'] > 80 or predictions.get('predicted_cpu', 0) > 85:
                confidence = self._calculate_recommendation_confidence(trends, 'cpu')
                if confidence > self.confidence_threshold:
                    recommendations.append(OptimizationRecommendation(
                        action="scale_up",
                        target_service=service,
                        confidence=confidence,
                        expected_improvement=30.0,
                        reasoning=f"High CPU usage detected ({trends['avg_cpu']:.1f}% avg, predicted {predictions.get('predicted_cpu', 0):.1f}%)",
                        priority="high"
                    ))
            
            # High memory usage recommendation
            if trends['avg_memory'] > 85 or predictions.get('predicted_memory', 0) > 90:
                confidence = self._calculate_recommendation_confidence(trends, 'memory')
                if confidence > self.confidence_threshold:
                    recommendations.append(OptimizationRecommendation(
                        action="restart_or_scale",
                        target_service=service,
                        confidence=confidence,
                        expected_improvement=25.0,
                        reasoning=f"High memory usage detected ({trends['avg_memory']:.1f}% avg, predicted {predictions.get('predicted_memory', 0):.1f}%)",
                        priority="high"
                    ))
            
            # High response time recommendation
            if trends['avg_response'] > 2000 or predictions.get('predicted_response', 0) > 2500:
                confidence = self._calculate_recommendation_confidence(trends, 'response')
                if confidence > self.confidence_threshold:
                    recommendations.append(OptimizationRecommendation(
                        action="optimize_or_scale",
                        target_service=service,
                        confidence=confidence,
                        expected_improvement=40.0,
                        reasoning=f"High response time detected ({trends['avg_response']:.1f}ms avg, predicted {predictions.get('predicted_response', 0):.1f}ms)",
                        priority="medium"
                    ))
            
            # Increasing error rate recommendation
            if trends['error_trend'] > 0.5:  # Error rate increasing
                confidence = self._calculate_recommendation_confidence(trends, 'error')
                if confidence > self.confidence_threshold:
                    recommendations.append(OptimizationRecommendation(
                        action="investigate_or_restart",
                        target_service=service,
                        confidence=confidence,
                        expected_improvement=50.0,
                        reasoning=f"Increasing error rate detected (trend: {trends['error_trend']:.2f})",
                        priority="high"
                    ))
            
            # Low utilization recommendation (scale down)
            if trends['avg_cpu'] < 20 and trends['avg_memory'] < 30:
                confidence = self._calculate_recommendation_confidence(trends, 'utilization')
                if confidence > self.confidence_threshold:
                    recommendations.append(OptimizationRecommendation(
                        action="scale_down",
                        target_service=service,
                        confidence=confidence,
                        expected_improvement=20.0,
                        reasoning=f"Low utilization detected (CPU: {trends['avg_cpu']:.1f}%, Memory: {trends['avg_memory']:.1f}%)",
                        priority="low"
                    ))
        
        # Sort by priority and confidence
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda r: (priority_order.get(r.priority, 0), r.confidence), reverse=True)
        
        return recommendations
    
    def _calculate_recommendation_confidence(self, trends: Dict[str, float], metric_type: str) -> float:
        """Calculate confidence in a recommendation"""
        if not trends:
            return 0.0
        
        # Base confidence on data availability
        service_metrics = [m for m in self.metrics_history if m.service_name == trends.get('service_name', '')]
        data_confidence = min(1.0, len(service_metrics) / 100)
        
        # Adjust based on metric stability
        if metric_type == 'cpu':
            metric_value = trends['avg_cpu']
            stability = 1.0 - abs(metric_value - 50) / 50  # Closer to 50% = more stable
        elif metric_type == 'memory':
            metric_value = trends['avg_memory']
            stability = 1.0 - abs(metric_value - 50) / 50
        elif metric_type == 'response':
            metric_value = trends['avg_response']
            stability = 1.0 - min(1.0, metric_value / 5000)  # Lower response time = more stable
        elif metric_type == 'error':
            stability = 1.0 - min(1.0, trends['avg_error'] / 10)  # Lower error rate = more stable
        elif metric_type == 'utilization':
            metric_value = (trends['avg_cpu'] + trends['avg_memory']) / 2
            stability = 1.0 - abs(metric_value - 25) / 25  # Lower utilization = more stable
        else:
            stability = 0.5
        
        return (data_confidence + stability) / 2
    
    def apply_optimization(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply an optimization recommendation"""
        logger.info(f"Applying optimization: {recommendation.action} for {recommendation.target_service}")
        
        try:
            if recommendation.action == "scale_up":
                return self._scale_service(recommendation.target_service, "up")
            elif recommendation.action == "scale_down":
                return self._scale_service(recommendation.target_service, "down")
            elif recommendation.action == "restart_or_scale":
                return self._restart_service(recommendation.target_service)
            elif recommendation.action == "investigate_or_restart":
                return self._investigate_and_restart(recommendation.target_service)
            elif recommendation.action == "optimize_or_scale":
                return self._optimize_service(recommendation.target_service)
            else:
                logger.warning(f"Unknown optimization action: {recommendation.action}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to apply optimization: {e}")
            return False
    
    def _scale_service(self, service_name: str, direction: str) -> bool:
        """Scale a service up or down"""
        try:
            if direction == "up":
                # Scale up (add replica)
                result = subprocess.run([
                    'docker-compose', '-f', 'docker-compose.production.yml',
                    'up', '-d', '--scale', f'{service_name}=2'
                ], capture_output=True, text=True, timeout=60)
            else:
                # Scale down (remove replica)
                result = subprocess.run([
                    'docker-compose', '-f', 'docker-compose.production.yml',
                    'up', '-d', '--scale', f'{service_name}=1'
                ], capture_output=True, text=True, timeout=60)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to scale {service_name}: {e}")
            return False
    
    def _restart_service(self, service_name: str) -> bool:
        """Restart a service"""
        try:
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose.production.yml',
                'restart', service_name
            ], capture_output=True, text=True, timeout=60)
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to restart {service_name}: {e}")
            return False
    
    def _investigate_and_restart(self, service_name: str) -> bool:
        """Investigate and restart a service"""
        logger.info(f"Investigating {service_name} before restart")
        
        # Collect diagnostic information
        try:
            # Get container logs
            result = subprocess.run([
                'docker', 'logs', '--tail', '50', f'forge-{service_name}-prod'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                log_file = f"/tmp/{service_name}-investigation-{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                with open(log_file, 'w') as f:
                    f.write(result.stdout)
                logger.info(f"Investigation logs saved to {log_file}")
            
            # Restart the service
            return self._restart_service(service_name)
            
        except Exception as e:
            logger.error(f"Failed to investigate {service_name}: {e}")
            return False
    
    def _optimize_service(self, service_name: str) -> bool:
        """Optimize a service configuration"""
        logger.info(f"Optimizing {service_name}")
        
        # For now, just restart the service (could be expanded with specific optimizations)
        return self._restart_service(service_name)
    
    def run_optimization_cycle(self) -> Dict[str, any]:
        """Run a complete optimization cycle"""
        logger.info("Starting AI optimization cycle")
        
        # Collect current metrics
        current_metrics = self.collect_metrics()
        self.metrics_history.extend(current_metrics)
        
        # Keep only recent data (last 1000 data points per service)
        if len(self.metrics_history) > 5000:  # Approximate limit
            self.metrics_history = self.metrics_history[-5000:]
        
        # Generate recommendations
        recommendations = self.generate_optimization_recommendations()
        
        # Apply top recommendations
        applied_recommendations = []
        for recommendation in recommendations[:3]:  # Apply top 3 recommendations
            if self.apply_optimization(recommendation):
                applied_recommendations.append(recommendation)
                logger.info(f"Applied recommendation: {recommendation.action} for {recommendation.target_service}")
        
        # Save data
        self._save_data()
        
        # Generate summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'metrics_collected': len(current_metrics),
            'total_recommendations': len(recommendations),
            'applied_recommendations': len(applied_recommendations),
            'recommendations': [
                {
                    'action': r.action,
                    'target_service': r.target_service,
                    'confidence': r.confidence,
                    'priority': r.priority,
                    'reasoning': r.reasoning
                } for r in recommendations
            ]
        }
        
        return summary
    
    def get_optimization_report(self) -> Dict[str, any]:
        """Get a comprehensive optimization report"""
        services = list(set(m.service_name for m in self.metrics_history))
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_data_points': len(self.metrics_history),
            'services_analyzed': len(services),
            'service_analysis': {}
        }
        
        for service in services:
            trends = self.analyze_performance_trends(service)
            predictions = self.predict_resource_needs(service)
            
            report['service_analysis'][service] = {
                'trends': trends,
                'predictions': predictions,
                'data_points': len([m for m in self.metrics_history if m.service_name == service])
            }
        
        return report

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-Driven Optimization for MCP Gateway')
    parser.add_argument('--collect', action='store_true', help='Collect metrics only')
    parser.add_argument('--analyze', action='store_true', help='Analyze trends and generate recommendations')
    parser.add_argument('--optimize', action='store_true', help='Run optimization cycle')
    parser.add_argument('--report', action='store_true', help='Generate optimization report')
    parser.add_argument('--service', help='Specific service to analyze')
    parser.add_argument('--interval', type=int, default=300, help='Optimization interval in seconds')
    
    args = parser.parse_args()
    
    optimizer = AIOptimizationEngine()
    
    if args.collect:
        metrics = optimizer.collect_metrics()
        print(f"Collected {len(metrics)} metrics")
        
    elif args.analyze:
        if args.service:
            trends = optimizer.analyze_performance_trends(args.service)
            predictions = optimizer.predict_resource_needs(args.service)
            print(f"Analysis for {args.service}:")
            print(f"Trends: {trends}")
            print(f"Predictions: {predictions}")
        else:
            recommendations = optimizer.generate_optimization_recommendations()
            print(f"Generated {len(recommendations)} recommendations")
            for rec in recommendations:
                print(f"- {rec.action} for {rec.target_service} (confidence: {rec.confidence:.2f}, priority: {rec.priority})")
                
    elif args.optimize:
        summary = optimizer.run_optimization_cycle()
        print(f"Optimization cycle completed:")
        print(f"- Metrics collected: {summary['metrics_collected']}")
        print(f"- Recommendations generated: {summary['total_recommendations']}")
        print(f"- Recommendations applied: {summary['applied_recommendations']}")
        
    elif args.report:
        report = optimizer.get_optimization_report()
        print(json.dumps(report, indent=2))
        
    else:
        # Default: run optimization cycle
        summary = optimizer.run_optimization_cycle()
        print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()