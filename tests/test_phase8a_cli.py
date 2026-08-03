from main import build_parser

def test_trade_commands_parse():
    p=build_parser()
    assert p.parse_args(["trade","account"]).trade_command=="account"
    assert p.parse_args(["trade","positions"]).trade_command=="positions"
    assert p.parse_args(["trade","orders","--days","7"]).days==7
    args=p.parse_args(["trade","plan","SPY","--quantity","2"])
    assert args.symbol=="SPY" and args.quantity==2
    assert p.parse_args(["trade","validate","SPY"]).trade_command=="validate"
