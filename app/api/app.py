from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.schemas import *
from app.api import services


def create_api(*, settings_path: str='data/local_settings.json') -> FastAPI:
    app=FastAPI(title='TradingEngine Operator API',version='1.0.0-alpha.1')
    app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:5173','http://localhost:5173'],allow_methods=['*'],allow_headers=['*'])

    @app.get('/api/health', response_model=HealthResponse)
    def health():
        try: return services.health_payload()
        except Exception as exc: raise HTTPException(500,str(exc)) from exc

    @app.get('/api/accounts', response_model=AccountListResponse)
    def accounts():
        try:
            linked,local=services.list_accounts(settings_path)
            return {'accounts':[{'masked_id':'****'+a.account_id[-4:],'account_type':a.account_type,
                'selected':a.account_id[-4:]==local.selected_account_last_four} for a in linked],
                'selected_last_four':local.selected_account_last_four or None}
        except Exception as exc: raise HTTPException(502,str(exc)) from exc

    @app.post('/api/accounts/select', response_model=AccountView)
    def select_account(request: AccountSelectionRequest):
        try:
            a=services.save_account(request.last_four, settings_path)
            return {'masked_id':'****'+a.account_id[-4:],'account_type':a.account_type,'selected':True}
        except Exception as exc: raise HTTPException(400,str(exc)) from exc

    @app.post('/api/backtests', response_model=BacktestResponse)
    def backtest(request: BacktestRequest):
        try: return services.run_backtest(request)
        except ValueError as exc: raise HTTPException(400,str(exc)) from exc
        except Exception as exc: raise HTTPException(502,str(exc)) from exc

    @app.post('/api/recommendations', response_model=RecommendationResponse)
    def recommendations(request: RecommendationRequest):
        try: return services.run_recommendations(request)
        except ValueError as exc: raise HTTPException(400,str(exc)) from exc
        except Exception as exc: raise HTTPException(502,str(exc)) from exc

    @app.post('/api/orders/submit')
    def blocked_submission():
        raise HTTPException(403,'Live order submission is not available in this release.')
    return app

app=create_api()
