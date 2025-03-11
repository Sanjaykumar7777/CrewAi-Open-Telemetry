from crewai import Agent, Task, Crew
import subprocess
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader


trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
span_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(span_exporter))

metrics.set_meter_provider(MeterProvider(
    metric_readers=[PeriodicExportingMetricReader(OTLPMetricExporter(endpoint="http://localhost:4317"))]
))

meter = metrics.get_meter(__name__)
latency_metric = meter.create_histogram("network_latency", unit="ms")
packet_usage_metric = meter.create_counter("packet_usage", unit="packets")


def measure_latency():
    with tracer.start_as_current_span("network_latency_measurement"):
        try:
            result = subprocess.run(['ping', '-c', '4', 'google.com'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if "time=" in line:
                    latency = float(line.split('time=')[1].split(' ')[0])
                    latency_metric.record(latency)
                    print(f"[NetworkLatencyAgent] Measured latency: {latency} ms")
                    return latency
        except Exception as e:
            print(f"[NetworkLatencyAgent] Error measuring latency: {e}")
            return None

network_latency_agent = Agent(
    role="Network Monitor",
    goal="Measure network latency and report the results.",
    backstory="You are a network monitoring expert collecting latency data.",
    verbose=True,
    allow_delegation=False
)

task_latency = Task(
    description="Measure network latency and return the value in milliseconds.",
    agent=network_latency_agent,
    expected_output="A numerical latency value in ms.",
    function=measure_latency
)

# Packet Usage Agent
def measure_packet_usage():
    with tracer.start_as_current_span("packet_usage_measurement"):
        try:
            result = subprocess.run(['netstat', '-s'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            for line in lines:
                if "packets received" in line:
                    packets = int(line.strip().split(' ')[0])
                    packet_usage_metric.add(packets)
                    print(f"[PacketUsageAgent] Measured packet usage: {packets} packets")
                    return packets
        except Exception as e:
            print(f"[PacketUsageAgent] Error measuring packet usage: {e}")
            return None

packet_usage_agent = Agent(
    role="Packet Monitor",
    goal="Monitor packet usage and report the results.",
    backstory="You are responsible for tracking network packet usage.",
    verbose=True,
    allow_delegation=False
)

task_packet_usage = Task(
    description="Measure packet usage and return the count.",
    agent=packet_usage_agent,
    expected_output="A numerical count of packets used.",
    function=measure_packet_usage
)

# Orchestrator Agent
def orchestrate_tasks():
    print("[OrchestratorAgent] Checking agent status...")
    latency = task_latency.run()
    packets = task_packet_usage.run()
    report = {"network_latency": latency, "packet_usage": packets}
    print("[OrchestratorAgent] Final Report:", report)
    return report

orchestrator_agent = Agent(
    role="Orchestrator",
    goal="Manage all agents and ensure they execute their tasks correctly.",
    backstory="You oversee network monitoring and ensure smooth operation of monitoring agents.",
    verbose=True,
    allow_delegation=True
)

task_orchestrator = Task(
    description="Run the monitoring agents and consolidate their results.",
    agent=orchestrator_agent,
    expected_output="A summary report containing latency and packet usage.",
    function=orchestrate_tasks
)


crew = Crew(
    agents=[network_latency_agent, packet_usage_agent, orchestrator_agent],
    tasks=[task_latency, task_packet_usage, task_orchestrator]
)

if __name__ == "__main__":
    print("[System] Running AI Agents...")
    crew.kickoff()
