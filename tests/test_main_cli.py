import pytest

from main import _portfolio_from_args, build_parser


def test_scan_parser_accepts_multiple_symbols_and_strategy():
    args = build_parser().parse_args([
        "scan", "spy", "qqq", "--strategy", "Conservative"
    ])
    assert args.command == "scan"
    assert args.symbols == ["spy", "qqq"]
    assert args.strategy == "Conservative"


def test_portfolio_arguments_must_be_supplied_together():
    args = build_parser().parse_args([
        "scan", "SPY", "--account-value", "100000"
    ])
    with pytest.raises(ValueError, match="supplied together"):
        _portfolio_from_args(args)


def test_research_and_paper_commands_parse():
    parser = build_parser()
    portfolio = parser.parse_args(["portfolio-backtest", "SPY", "QQQ"])
    assert portfolio.symbols == ["SPY", "QQQ"]
    walk = parser.parse_args(["walk-forward", "SPY"])
    assert walk.training_bars == 504
    paper = parser.parse_args([
        "paper", "--ledger", "paper.json", "open", "SPY",
        "--expiration", "2027-01-15", "--short", "700",
        "--long", "695", "--credit", "1.25",
    ])
    assert paper.paper_command == "open"
    assert paper.short == 700


def test_paper_scan_command_parses_symbols_and_quantity():
    args = build_parser().parse_args([
        "paper", "--ledger", "paper.json", "scan", "SPY", "QQQ",
        "--strategy", "Conservative", "--quantity", "2",
    ])
    assert args.paper_command == "scan"
    assert args.symbols == ["SPY", "QQQ"]
    assert args.strategy == "Conservative"
    assert args.quantity == 2
