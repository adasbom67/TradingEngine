class SchwabTradingError(RuntimeError):
    pass

class SchwabTradingConfigurationError(SchwabTradingError):
    pass

class SchwabTradingResponseError(SchwabTradingError):
    pass
