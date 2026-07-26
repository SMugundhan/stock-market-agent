from opentelemetry import trace

from opentelemetry.sdk.trace import TracerProvider

from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry.sdk.resources import Resource

import os

def setup_tracing ( service_name : str = "stock-market-agent" ) :

    """
    Sets up OpenTelemetry tracing, exporting spans to Tempo via OTLP.
    Call this once at app startup (in main.py's lifespan).
    """

    if os . getenv ( "OTEL_EXPORTER_ENABLED", "false" ) . lower () != "true" :

        print ( "Tracing disabled ( TEL_EXPORTER_ENABLED not set ) ---- skipping Tempo setup" )

        return trace . get_tracer ( service_name )  # return no-op tracer, safe to use everywhere

    resource = Resource . create ( { "service.name" : service_name } )

    provider = TracerProvider ( resource = resource )


    # in Docker , "tempo" resolves via the service name ( Same pattern as redis )

    exporter = OTLPSpanExporter ( endpoint = "http://tempo:4317", insecure = True )

    provider . add_span_processor ( BatchSpanProcessor ( exporter ) )

    trace . set_tracer_provider ( provider )

    return trace . get_tracer ( service_name )


tracer = None  # set by setup_tracing () at startup

