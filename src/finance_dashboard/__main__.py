"""CLI entrypoint for Finance Dashboard.

Run with: python -m finance_dashboard --config pipeline.yml
Or: finance-dashboard --config pipeline.yml (after installation)
"""

import argparse
import logging
import sys

from finance_dashboard.main import FinanceDashboard
from finance_dashboard.pipeline_config import PipelineConfig


def setup_logging(level: str = "INFO"):
    """Set up basic logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    """Run main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Finance Dashboard - Collect and store financial data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  finance-dashboard --config pipeline.yml
  finance-dashboard --config examples/pipeline-simple.yml
  python -m finance_dashboard --config pipeline.yml

Configuration:
  Copy examples/pipeline-simple.yml to pipeline.yml and customize it.
  Set environment variables for credentials (see .env.dist).
        """,
    )

    parser.add_argument("--config", "-c", type=str, required=True, help="Path to pipeline YAML configuration file")

    parser.add_argument(
        "--validate-only", action="store_true", help="Only validate configuration without running the pipeline"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override log level from configuration",
    )

    args = parser.parse_args()

    # Load pipeline configuration
    try:
        pipeline_config = PipelineConfig(args.config)
    except FileNotFoundError:
        return 1
    except Exception:
        return 1

    # Setup logging
    log_level = args.log_level or pipeline_config.log_level
    setup_logging(log_level)

    logger = logging.getLogger(__name__)
    logger.info(f"Loading pipeline configuration from: {args.config}")

    # Validate configuration
    validation_errors = pipeline_config.validate()
    if validation_errors:
        for _error in validation_errors:
            pass
        return 1

    logger.info("✅ Configuration validation passed")

    if args.validate_only:
        return 0

    # Run the pipeline
    try:
        dashboard = FinanceDashboard(pipeline_config)
        dashboard.run()
        return 0
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
