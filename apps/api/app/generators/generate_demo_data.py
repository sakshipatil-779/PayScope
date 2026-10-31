"""CLI command to generate synthetic dataset files."""
import argparse
from pathlib import Path
import sys
from app.generators.config import GeneratorConfig
from app.generators.dataset_generator import DatasetGenerator
from app.generators.export_generator import export_dataset


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic financial demo data for MandateLens.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="sample_data",
        help="Target directory for generated files (CSV, XLSX, JSON).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation (default: 42).",
    )

    args = parser.parse_args()

    # Resolve output directory
    target_path = Path(args.output_dir)
    if not target_path.is_absolute():
        # Find repository root (folder containing MandateLens_Project_Docs)
        candidate = Path(__file__).resolve()
        repo_root = None
        for p in candidate.parents:
            if (p / "MandateLens_Project_Docs").exists():
                repo_root = p
                break
        if repo_root:
            target_path = repo_root / args.output_dir
        else:
            target_path = Path.cwd() / args.output_dir

    print(f"Generating synthetic dataset with seed {args.seed}...")
    config = GeneratorConfig(seed=args.seed)
    generator = DatasetGenerator(config)
    dataset = generator.generate()

    exported = export_dataset(dataset, target_path)

    manifest = dataset["manifest"]
    summary = manifest["summary"]
    print(f"Successfully generated synthetic dataset in: {target_path}")
    print(f"- Bank Statement Transactions: {summary['transaction_count']}")
    print(f"- Payment Notifications: {summary['notification_count']}")
    print(f"- Total Debits: {manifest['currency']} {summary['total_debit_amount']}")
    print(f"- Total Credits: {manifest['currency']} {summary['total_credit_amount']}")
    print(f"- Files created:")
    for key, path in exported.items():
        print(f"  * {key}: {path.name} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
