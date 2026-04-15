import time
from collections import defaultdict

# A simple mock metrics system compatible with Prometheus exposition format
class MetricsService:
    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        
    def inc_counter(self, name: str, value: int = 1):
        self.counters[name] += value
        
    def observe(self, name: str, value: float):
        self.histograms[name].append(value)
        
    def generate_metrics(self) -> str:
        lines = []
        for name, value in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
            
        for name, values in self.histograms.items():
            if not values:
                continue
            lines.append(f"# TYPE {name} summary")
            avg = sum(values) / len(values)
            lines.append(f"{name}_sum {sum(values)}")
            lines.append(f"{name}_count {len(values)}")
            
        return "\n".join(lines) + "\n"

metrics_service = MetricsService()

def generate_latest_metrics() -> str:
    return metrics_service.generate_metrics()
