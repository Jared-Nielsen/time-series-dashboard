import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, Union
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.stats.diagnostic import acorr_ljungbox
from pmdarima import auto_arima
import warnings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ARIMAForecaster:
    def __init__(
        self,
        seasonal: bool = True,
        seasonal_period: Optional[int] = None,
        auto_select: bool = True,
        max_p: int = 5,
        max_q: int = 5,
        max_d: int = 2,
        max_P: int = 2,
        max_Q: int = 2,
        max_D: int = 1,
        information_criterion: str = 'aic',
        alpha: float = 0.05
    ):
        self.seasonal = seasonal
        self.seasonal_period = seasonal_period
        self.auto_select = auto_select
        self.max_p = max_p
        self.max_q = max_q
        self.max_d = max_d
        self.max_P = max_P
        self.max_Q = max_Q
        self.max_D = max_D
        self.information_criterion = information_criterion
        self.alpha = alpha
        
        self.model = None
        self.fitted_model = None
        self.order = None
        self.seasonal_order = None
        self.residuals = None
        self.fitted_values = None
        self.train_data = None
        self.frequency = None
        
    def detect_seasonality(self, data: pd.Series, max_lag: int = 48) -> Optional[int]:
        if len(data) < 2 * max_lag:
            logger.warning("Insufficient data for seasonality detection")
            return None
            
        acf_values = acf(data, nlags=max_lag, fft=True)
        
        seasonal_periods = []
        threshold = 0.3
        
        for freq in [24, 7, 12, 52, 365]:
            if freq <= max_lag and freq < len(data) / 2:
                if abs(acf_values[freq]) > threshold:
                    seasonal_periods.append(freq)
        
        if seasonal_periods:
            period = seasonal_periods[0]
            logger.info(f"Detected seasonal period: {period}")
            return period
            
        return None
    
    def check_stationarity(self, data: pd.Series) -> Dict[str, Any]:
        result = adfuller(data, autolag='AIC')
        
        return {
            'adf_statistic': result[0],
            'p_value': result[1],
            'critical_values': result[4],
            'is_stationary': result[1] < 0.05
        }
    
    def difference_data(self, data: pd.Series, d: int = 1) -> pd.Series:
        diff_data = data.copy()
        for _ in range(d):
            diff_data = diff_data.diff().dropna()
        return diff_data
    
    def auto_select_parameters(self, data: pd.Series) -> Tuple[Tuple[int, int, int], Optional[Tuple[int, int, int, int]]]:
        logger.info("Auto-selecting ARIMA parameters...")
        
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            
            # Ensure we have a valid seasonal period
            if self.seasonal and self.seasonal_period is None:
                self.seasonal_period = 24  # Default to daily seasonality for hourly data
                logger.info(f"Using default seasonal period: {self.seasonal_period}")
            
            auto_model = auto_arima(
                data,
                start_p=0, max_p=self.max_p,
                start_q=0, max_q=self.max_q,
                max_d=self.max_d,
                start_P=0, max_P=self.max_P if self.seasonal else 0,
                start_Q=0, max_Q=self.max_Q if self.seasonal else 0,
                max_D=self.max_D if self.seasonal else 0,
                seasonal=self.seasonal,
                m=self.seasonal_period if self.seasonal else 1,
                information_criterion=self.information_criterion,
                stepwise=True,
                suppress_warnings=True,
                error_action='ignore',
                n_jobs=-1
            )
            
            order = auto_model.order
            seasonal_order = auto_model.seasonal_order if self.seasonal else None
            
        logger.info(f"Selected order: {order}")
        if seasonal_order:
            logger.info(f"Selected seasonal order: {seasonal_order}")
            
        return order, seasonal_order
    
    def fit(
        self,
        data: Union[pd.Series, np.ndarray],
        order: Optional[Tuple[int, int, int]] = None,
        seasonal_order: Optional[Tuple[int, int, int, int]] = None,
        exog: Optional[Union[pd.DataFrame, np.ndarray]] = None
    ) -> 'ARIMAForecaster':
        
        if isinstance(data, np.ndarray):
            data = pd.Series(data)
        
        self.train_data = data.copy()
        
        if pd.api.types.is_datetime64_any_dtype(data.index):
            self.frequency = pd.infer_freq(data.index)
        
        stationarity_check = self.check_stationarity(data)
        if not stationarity_check['is_stationary']:
            logger.warning("Data is not stationary. Model may benefit from differencing.")
        
        if self.seasonal and self.seasonal_period is None:
            self.seasonal_period = self.detect_seasonality(data)
        
        if self.auto_select and order is None:
            self.order, self.seasonal_order = self.auto_select_parameters(data)
        else:
            self.order = order if order else (1, 1, 1)
            self.seasonal_order = seasonal_order
        
        if self.seasonal and self.seasonal_order:
            logger.info(f"Fitting SARIMAX model with order {self.order} and seasonal order {self.seasonal_order}")
            self.model = SARIMAX(
                data,
                order=self.order,
                seasonal_order=self.seasonal_order,
                exog=exog,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
        else:
            logger.info(f"Fitting ARIMA model with order {self.order}")
            self.model = ARIMA(
                data,
                order=self.order,
                exog=exog,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
        
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore')
            self.fitted_model = self.model.fit()
        
        self.residuals = self.fitted_model.resid
        self.fitted_values = self.fitted_model.fittedvalues
        
        logger.info(f"Model AIC: {self.fitted_model.aic:.2f}")
        logger.info(f"Model BIC: {self.fitted_model.bic:.2f}")
        
        return self
    
    def forecast(
        self,
        steps: int,
        exog: Optional[Union[pd.DataFrame, np.ndarray]] = None,
        return_conf_int: bool = True
    ) -> Dict[str, Any]:
        
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before forecasting")
        
        forecast_result = self.fitted_model.forecast(steps=steps, exog=exog)
        
        result = {
            'forecast': forecast_result,
            'steps': steps
        }
        
        if return_conf_int:
            forecast_df = self.fitted_model.get_forecast(steps=steps, exog=exog)
            conf_int = forecast_df.conf_int(alpha=self.alpha)
            
            result['lower_bound'] = conf_int.iloc[:, 0]
            result['upper_bound'] = conf_int.iloc[:, 1]
            result['confidence_level'] = 1 - self.alpha
        
        if hasattr(forecast_result, 'index') and self.frequency:
            result['index'] = forecast_result.index
        else:
            last_index = self.train_data.index[-1] if hasattr(self.train_data, 'index') else len(self.train_data) - 1
            if pd.api.types.is_datetime64_any_dtype(self.train_data.index):
                freq = self.frequency or 'H'
                future_index = pd.date_range(
                    start=last_index + pd.Timedelta(1, unit='H'),
                    periods=steps,
                    freq=freq
                )
                result['index'] = future_index
            else:
                result['index'] = range(last_index + 1, last_index + steps + 1)
        
        return result
    
    def rolling_forecast(
        self,
        data: pd.Series,
        initial_train_size: int,
        horizon: int,
        step_size: int = 1,
        refit_interval: Optional[int] = None
    ) -> Dict[str, Any]:
        
        n_forecasts = (len(data) - initial_train_size - horizon + 1) // step_size
        
        if n_forecasts <= 0:
            raise ValueError("Insufficient data for rolling forecast with given parameters")
        
        forecasts = []
        actuals = []
        lower_bounds = []
        upper_bounds = []
        forecast_dates = []
        
        for i in range(0, n_forecasts * step_size, step_size):
            train_end = initial_train_size + i
            test_start = train_end
            test_end = test_start + horizon
            
            if test_end > len(data):
                break
            
            train_data = data.iloc[:train_end]
            test_data = data.iloc[test_start:test_end]
            
            if refit_interval is None or i % refit_interval == 0:
                self.fit(train_data)
            else:
                # For now, always refit - append is not working with index issues
                self.fit(train_data)
            
            forecast_result = self.forecast(steps=horizon, return_conf_int=True)
            
            forecasts.append(forecast_result['forecast'].values)
            actuals.append(test_data.values)
            lower_bounds.append(forecast_result['lower_bound'].values)
            upper_bounds.append(forecast_result['upper_bound'].values)
            
            if hasattr(test_data, 'index'):
                forecast_dates.append(test_data.index)
        
        return {
            'forecasts': np.array(forecasts),
            'actuals': np.array(actuals),
            'lower_bounds': np.array(lower_bounds),
            'upper_bounds': np.array(upper_bounds),
            'dates': forecast_dates if forecast_dates else None,
            'horizon': horizon,
            'n_windows': len(forecasts)
        }
    
    def get_model_diagnostics(self) -> Dict[str, Any]:
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before getting diagnostics")
        
        ljung_box = acorr_ljungbox(self.residuals, lags=10, return_df=True)
        
        residual_acf = acf(self.residuals, nlags=20)
        residual_pacf = pacf(self.residuals, nlags=20)
        
        return {
            'summary': self.fitted_model.summary(),
            'aic': self.fitted_model.aic,
            'bic': self.fitted_model.bic,
            'ljung_box': ljung_box,
            'residual_mean': np.mean(self.residuals),
            'residual_std': np.std(self.residuals),
            'residual_acf': residual_acf,
            'residual_pacf': residual_pacf,
            'order': self.order,
            'seasonal_order': self.seasonal_order
        }
    
    def predict(
        self,
        start: Optional[int] = None,
        end: Optional[int] = None,
        dynamic: bool = False
    ) -> pd.Series:
        
        if self.fitted_model is None:
            raise ValueError("Model must be fitted before prediction")
        
        return self.fitted_model.predict(start=start, end=end, dynamic=dynamic)
    
    def get_params(self) -> Dict[str, Any]:
        return {
            'order': self.order,
            'seasonal_order': self.seasonal_order,
            'seasonal_period': self.seasonal_period,
            'aic': self.fitted_model.aic if self.fitted_model else None,
            'bic': self.fitted_model.bic if self.fitted_model else None,
            'model_type': 'SARIMAX' if self.seasonal_order else 'ARIMA'
        }