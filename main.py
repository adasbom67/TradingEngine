from app.config.strategy_config import PutSpreadConfig


def main() -> None:
    """Test the put-spread strategy configuration."""

    config = PutSpreadConfig()

    config.validate()

    print("Configuration is valid.")
    print(config)


if __name__ == "__main__":
    main()