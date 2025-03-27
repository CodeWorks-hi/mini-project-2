import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import platform
import os
import joblib
from sklearn.metrics import r2_score
import matplotlib.dates as mdates
import tensorflow as tf


# 한글 폰트 조정
plt.rcParams["axes.unicode_minus"] = False

if platform.system() == "Darwin":  # macOS
    rc("font", family="AppleGothic")
elif platform.system() == "Windows":  # Windows
    font_path = "C:/Windows/Fonts/malgun.ttf"  # 맑은 고딕
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    rc("font", family=font_name)
elif platform.system() == "Linux":  # Linux (Ubuntu, Docker 등)
    font_path = "fonts/NanumGothic.ttf"
    if not os.path.exists(font_path):
        st.error("NanumGothic.ttf 폰트 파일이 존재하지 않습니다. 'fonts' 폴더 내에 폰트 파일을 확인하세요.")
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    rc("font", family=font_name)


st.title("AI 판매 예측 시스템")

def prediction_ui():

    tab1, tab2, tab3 = st.tabs(["지역별 수출량 예측", "차종별 판매량 예측", "공장별 판매량 예측"])

    with tab1:
        # 1. 지역별 예측 시스템
        # 1-1. 데이터 준비 함수
        def prepare_lstm_data(series, time_steps=12):
            values = series['y'].values.reshape(-1, 1)
            scaler = MinMaxScaler()
            scaled = scaler.fit_transform(values)

            X, y = [], []
            for i in range(time_steps, len(scaled)):
                X.append(scaled[i-time_steps:i])
                y.append(scaled[i])
            X, y = np.array(X), np.array(y)
            return X, y, scaler

        # 1-2. 모델 정의 및 학습
        def train_lstm_model(X, y, units=50, epochs=600, batch_size=16, region_name=None):
            model = Sequential()
            model.add(LSTM(units=units, activation='relu', input_shape=(X.shape[1], X.shape[2])))
            model.add(Dense(1))
            model.compile(optimizer='adam', loss='mse')
            
            # 조기 종료를 위한 콜백 클래스 정의
            class EarlyStoppingByLoss(tf.keras.callbacks.Callback):
                def __init__(self, region_name):
                    super(EarlyStoppingByLoss, self).__init__()
                    self.region_name = region_name
                    
                def on_epoch_end(self, epoch, logs=None):
                    current_loss = logs.get('loss')
                    if current_loss is not None and current_loss <= 0.01:
                        print(f"\n🎉 조기 종료: epoch {epoch+1}에서 loss가 0.01 이하({current_loss:.4f})로 떨어짐")
                        # 모델 저장
                        model_path = get_model_path(self.region_name)
                        scaler_path = get_scaler_path(self.region_name)
                        self.model.save(model_path)
                        print(f"💾 모델이 {model_path}에 저장되었습니다.")
                        self.model.stop_training = True
            
            # 콜백 인스턴스 생성
            early_stopping = EarlyStoppingByLoss(region_name)
            
            history = model.fit(
                X, y, 
                epochs=epochs, 
                batch_size=batch_size, 
                verbose=1,
                callbacks=[early_stopping]
            )
            
            return model

        # 1-3. 미래 예측
        def forecast_lstm(model, series, forecast_months, scaler, time_steps=12):
            data = scaler.transform(series['y'].values.reshape(-1, 1))
            last_sequence = data[-time_steps:]

            predictions = []
            for _ in range(forecast_months):
                input_seq = last_sequence.reshape(1, time_steps, 1)
                pred = model.predict(input_seq, verbose=0)
                predictions.append(pred[0, 0])
                last_sequence = np.append(last_sequence[1:], pred, axis=0)

            forecast_scaled = np.array(predictions).reshape(-1, 1)
            forecast_values = scaler.inverse_transform(forecast_scaled)

            last_date = series.index[-1]
            future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_months, freq='MS')

            result = pd.DataFrame({
                '연도': future_dates.year,
                '월': future_dates.month,
                '예측 수출량': forecast_values.flatten()
            })
            return result

        # 1-4. 시각화 함수
        def plot_lstm_forecast(series, forecast_df, region_name, forecast_months):
            forecast_index = pd.to_datetime(forecast_df['연도'].astype(str) + '-' + forecast_df['월'].astype(str))
            forecast_values = forecast_df['예측 수출량'].values

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(series.index, series['y'], label='실제 수출량', color='black')
            ax.plot(forecast_index, forecast_values, label='LSTM 예측', color='red', linestyle='--')
            ax.axvline(x=series.index[-1], color='gray', linestyle=':', label='예측 시작점')
            ax.set_title(f"{region_name} LSTM 기반 수출량 예측")
            ax.set_xlabel("날짜")
            ax.set_ylabel("수출량")
            ax.legend()
            ax.grid(True)
            fig.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

            # 저장 경로 생성
            save_path = f"images/result/{region_name} LSTM 지역별 수출량 예측_{forecast_months}개월.png"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.savefig(save_path, dpi=300)

            # ✅ 세션 스테이트에 저장
            st.session_state["last_forecast_image"] = save_path

            st.success(f"그래프가 저장되었습니다: `{save_path}`")


        # 모델 및 스케일러 경로 함수
        def get_model_path(region_name):
            return f"models/lstm_region_{region_name}_model.h5"

        def get_scaler_path(region_name):
            return f"models/lstm_region_{region_name}_scaler.pkl"

        def ensure_model(region_name):
            model_path = get_model_path(region_name)
            scaler_path = get_scaler_path(region_name)

            if os.path.exists(model_path) and os.path.exists(scaler_path):
                print(f"✅ 저장된 모델과 스케일러가 존재합니다: {model_path}")
                return True
            else:
                print(f"🚀 모델 또는 스케일러가 존재하지 않아 새로 학습합니다.")
                return False
        # 1. 지역별 수출량 예측
        file_path = "data/processed/hyundai-by-region.csv"  # 현대만 할 거니까~
        df = pd.read_csv(file_path)

        region_list = ["선택하세요"] + list(df['지역명'].unique())
        region_name = st.selectbox("지역명을 선택하세요", region_list, key="region_list")
        forecast_months = st.number_input("몇 개월 뒤까지 예측할까요?", min_value=1, max_value=24, value=12, key="region_month")

        # 전처리: 지역명 Only -> 현대 데이터에 맞는 전처리
        df = df.drop(columns=['대륙'])
        cols = ['지역명'] + [col for col in df.columns if col != '지역명']
        df = df[cols]

        if st.button("지역별 수출량 예측 시작") :
            if region_name == "선택하세요":
                st.error("지역명을 선택해주세요.")
            else:
                region_data = df[df['지역명'] == region_name].iloc[:, 1:].T
                region_data.columns = ['y']
                region_data.index = pd.to_datetime(region_data.index)
                region_data = region_data.asfreq('MS')
                region_data['y'] = pd.to_numeric(region_data['y'], errors='coerce')
                region_data = region_data.dropna()

                status = ensure_model(region_name)

                # ✅ 특정 기간 값이 모두 0인지 확인
                zero_check_range = region_data.loc["2024-09":"2025-02", "y"]
                if zero_check_range.sum() == 0:
                    st.error("🚫 이 지역은 현재 검색이 불가능합니다.")
                else :
                    if status:
                        lstm_model = load_model(get_model_path(region_name), compile=False)
                        scaler = joblib.load(get_scaler_path(region_name))
                    else:
                        st.info("생성된 모델이 존재하지 않아 모델 생성을 시작합니다.")
                        st.info("30초 이상 소요될 수 있습니다.")
                        with st.spinner("🔄 모델을 학습 중입니다... 잠시만 기다려주세요."):
                            X, y, scaler = prepare_lstm_data(region_data)
                            lstm_model = train_lstm_model(X, y, region_name=region_name)
                            # 모델이 조기 종료되지 않은 경우에만 여기서 저장
                            if not os.path.exists(get_model_path(region_name)):
                                lstm_model.save(get_model_path(region_name))
                                joblib.dump(scaler, get_scaler_path(region_name))

                    lstm_forecast = forecast_lstm(lstm_model, region_data, forecast_months, scaler)
                    plot_lstm_forecast(region_data, lstm_forecast, region_name, forecast_months)
    with tab2:
        # 2. 차종별 판매량 예측
        def prepare_lstm_data(series, time_steps=12):
            values = series['y'].values.reshape(-1, 1)
            scaler = MinMaxScaler()
            scaled = scaler.fit_transform(values)

            X, y = [], []
            for i in range(time_steps, len(scaled)):
                X.append(scaled[i-time_steps:i])
                y.append(scaled[i])
            X, y = np.array(X), np.array(y)
            return X, y, scaler

        # 2. 모델 정의 및 학습
        def train_lstm_model(X, y, units=50, epochs=600, batch_size=16, car_name=None):
            model = Sequential()
            model.add(LSTM(units=units, activation='relu', input_shape=(X.shape[1], X.shape[2])))
            model.add(Dense(1))
            model.compile(optimizer='adam', loss='mse')
            
            # 조기 종료를 위한 콜백 클래스 정의
            class EarlyStoppingByLoss(tf.keras.callbacks.Callback):
                def __init__(self, car_name):
                    super(EarlyStoppingByLoss, self).__init__()
                    self.car_name = car_name
                    
                def on_epoch_end(self, epoch, logs=None):
                    current_loss = logs.get('loss')
                    if current_loss is not None and current_loss <= 0.01:
                        print(f"\n🎉 조기 종료: epoch {epoch+1}에서 loss가 0.01 이하({current_loss:.4f})로 떨어짐")
                        # 모델 저장
                        model_path = get_model_path(self.car_name)
                        scaler_path = get_scaler_path(self.car_name)
                        self.model.save(model_path)
                        print(f"💾 모델이 {model_path}에 저장되었습니다.")
                        self.model.stop_training = True
            
            # 콜백 인스턴스 생성
            early_stopping = EarlyStoppingByLoss(car_name)
            
            history = model.fit(
                X, y, 
                epochs=epochs, 
                batch_size=batch_size, 
                verbose=1,
                callbacks=[early_stopping]
            )
            
            return model

        # 3. 미래 예측
        def forecast_lstm(model, series, forecast_months, scaler, time_steps=12):
            data = scaler.transform(series['y'].values.reshape(-1, 1))
            last_sequence = data[-time_steps:]

            predictions = []
            for _ in range(forecast_months):
                input_seq = last_sequence.reshape(1, time_steps, 1)
                pred = model.predict(input_seq, verbose=0)
                predictions.append(pred[0, 0])
                last_sequence = np.append(last_sequence[1:], pred, axis=0)

            forecast_scaled = np.array(predictions).reshape(-1, 1)
            forecast_values = scaler.inverse_transform(forecast_scaled)

            last_date = series.index[-1]
            future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_months, freq='MS')

            result = pd.DataFrame({
                '연도': future_dates.year,
                '월': future_dates.month,
                '예측 판매량': forecast_values.flatten()
            })
            return result

        # 4. 시각화 함수
        def plot_lstm_forecast(series, forecast_df, car_name, forecast_months, save_path=None):
            forecast_index = pd.to_datetime(forecast_df['연도'].astype(str) + '-' + forecast_df['월'].astype(str))
            forecast_values = forecast_df['예측 판매량'].values

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(series.index, series['y'], label='실제 판매량', color='black')
            ax.plot(forecast_index, forecast_values, label='LSTM 예측', color='red', linestyle='--')
            ax.axvline(x=series.index[-1], color='gray', linestyle=':', label='예측 시작점')
            ax.set_title(f"{car_name} LSTM 기반 판매량 예측")
            ax.set_xlabel("날짜")
            ax.set_ylabel("판매량")
            ax.legend()
            ax.grid(True)
            fig.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

            # 저장 경로 생성
            save_path = f"images/result/{car_name} LSTM 지역별 수출량 예측_{forecast_months}개월.png"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.savefig(save_path, dpi=300)

            # ✅ 세션 스테이트에 저장
            st.session_state["last_forecast_image"] = save_path

            st.success(f"📊 그래프가 저장되었습니다: `{save_path}`")


        # 5. 실행 예시
        file_path = "data/processed/hyundai-by-car.csv"
        df = pd.read_csv(file_path)

        # 전처리: 인덱스 통합
        df['차종'] = df['차종'].astype(str) + '-' + df['거래 구분'].astype(str).str.zfill(2)
        df = df.drop(columns=['차량 유형', '거래 구분'])
        cols = ['차종'] + [col for col in df.columns if col != '차종']
        df = df[cols]

        car_list = ["선택하세요"] + list(set([x.split("-")[0] for x in df['차종'].unique()]))
        range_list = ["선택하세요"] + list(set([x.split("-")[1] for x in df['차종'].unique()]))
        car_name = st.selectbox("차종을 선택하세요.", car_list, key="car_list") + "-" + st.selectbox("거래 구분을 선택하세요.", range_list, key="range_list")
        forecast_months = st.number_input("몇 개월 뒤까지 예측할까요?", min_value=1, max_value=24, value=12, key="car_month")

        if st.button("차종별 판매량 예측 시작") :
            if "선택하세요" in car_name :
                st.error("차종과 거래 구분을 선택해주세요.")
            else:   
                car_data = df[df['차종'] == car_name].iloc[:, 1:].T
                if car_data.empty:
                    st.error("선택한 조건에 대한 데이터가 없습니다.")
                else:
                    car_data.columns = ['y']
                    car_data.index = pd.to_datetime(car_data.index)
                    car_data = car_data.asfreq('MS')
                    car_data['y'] = pd.to_numeric(car_data['y'], errors='coerce')
                    car_data = car_data.dropna()

                    def get_model_path(car_name):
                        return f"models/lstm_car_{car_name}_model.h5"

                    def get_scaler_path(car_name):
                        return f"models/lstm_car_{car_name}_scaler.pkl"

                    def ensure_model(car_name):
                        model_path = get_model_path(car_name)
                        scaler_path = get_scaler_path(car_name)

                        if os.path.exists(model_path) and os.path.exists(scaler_path):
                            print(f"✅ 저장된 모델과 스케일러가 존재합니다: {model_path}")
                            return True
                        else:
                            print(f"🚀 모델 또는 스케일러가 존재하지 않아 새로 학습합니다.")
                            return False

                    status = ensure_model(car_name)

                    # ✅ 특정 기간 값이 모두 0인지 확인
                    zero_check_range = car_data.loc["2024-09":"2025-02", "y"]
                    if zero_check_range.sum() == 0:
                        st.error("🚫 이 차는 더 이상 생산하지 않습니다.")
                    else :
                        if status:
                            lstm_model = load_model(get_model_path(car_name), compile=False)
                            scaler = joblib.load(get_scaler_path(car_name))
                        else:
                            st.info("생성된 모델이 존재하지 않아 모델 생성을 시작합니다.")
                            st.info("30초 이상 소요될 수 있습니다.")
                            with st.spinner("🔄 모델을 학습 중입니다... 잠시만 기다려주세요."):
                                X, y, scaler = prepare_lstm_data(car_data)
                                lstm_model = train_lstm_model(X, y, car_name=car_name)
                                # 모델이 조기 종료되지 않은 경우에만 여기서 저장
                                if not os.path.exists(get_model_path(car_name)):
                                    lstm_model.save(get_model_path(car_name))
                                    joblib.dump(scaler, get_scaler_path(car_name))

                        lstm_forecast = forecast_lstm(lstm_model, car_data, forecast_months, scaler)
                        plot_lstm_forecast(car_data, lstm_forecast, car_name, forecast_months)
    with tab3:
        # 공장별 판매량 예측
        # 1. 데이터 준비 함수
        def prepare_lstm_data(series, time_steps=12):
            values = series['y'].values.reshape(-1, 1)
            scaler = MinMaxScaler()
            scaled = scaler.fit_transform(values)

            X, y = [], []
            for i in range(time_steps, len(scaled)):
                X.append(scaled[i-time_steps:i])
                y.append(scaled[i])
            X, y = np.array(X), np.array(y)
            return X, y, scaler

        # 2. 모델 정의 및 학습
        def train_lstm_model(X, y, units=50, epochs=600, batch_size=16, plant_name=None):
            model = Sequential()
            model.add(LSTM(units=units, activation='relu', input_shape=(X.shape[1], X.shape[2])))
            model.add(Dense(1))
            model.compile(optimizer='adam', loss='mse')
            
            # 조기 종료를 위한 콜백 클래스 정의
            class EarlyStoppingByLoss(tf.keras.callbacks.Callback):
                def __init__(self, plant_name):
                    super(EarlyStoppingByLoss, self).__init__()
                    self.plant_name = plant_name
                    
                def on_epoch_end(self, epoch, logs=None):
                    current_loss = logs.get('loss')
                    if current_loss is not None and current_loss <= 0.01:
                        print(f"\n🎉 조기 종료: epoch {epoch+1}에서 loss가 0.01 이하({current_loss:.4f})로 떨어짐")
                        # 모델 저장
                        model_path = get_model_path(self.plant_name)
                        scaler_path = get_scaler_path(self.plant_name)
                        self.model.save(model_path)
                        print(f"💾 모델이 {model_path}에 저장되었습니다.")
                        self.model.stop_training = True
            
            # 콜백 인스턴스 생성
            early_stopping = EarlyStoppingByLoss(plant_name)
            
            history = model.fit(
                X, y, 
                epochs=epochs, 
                batch_size=batch_size, 
                verbose=1,
                callbacks=[early_stopping]
            )
            
            return model

        # 3. 미래 예측
        def forecast_lstm(model, series, forecast_months, scaler, time_steps=12):
            data = scaler.transform(series['y'].values.reshape(-1, 1))
            last_sequence = data[-time_steps:]

            predictions = []
            for _ in range(forecast_months):
                input_seq = last_sequence.reshape(1, time_steps, 1)
                pred = model.predict(input_seq, verbose=0)
                predictions.append(pred[0, 0])
                last_sequence = np.append(last_sequence[1:], pred, axis=0)

            forecast_scaled = np.array(predictions).reshape(-1, 1)
            forecast_values = scaler.inverse_transform(forecast_scaled)

            last_date = series.index[-1]
            future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_months, freq='MS')

            result = pd.DataFrame({
                '연도': future_dates.year,
                '월': future_dates.month,
                '예측 판매량': forecast_values.flatten()
            })
            return result

        # 4. 시각화 함수
        def plot_lstm_forecast(series, forecast_df, plant_name, forecast_months, save_path=None):
            forecast_index = pd.to_datetime(forecast_df['연도'].astype(str) + '-' + forecast_df['월'].astype(str))
            forecast_values = forecast_df['예측 판매량'].values

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(series.index, series['y'], label='실제 판매량', color='black')
            ax.plot(forecast_index, forecast_values, label='LSTM 예측', color='red', linestyle='--')
            ax.axvline(x=series.index[-1], color='gray', linestyle=':', label='예측 시작점')
            ax.set_title(f"{plant_name} LSTM 기반 판매량 예측")
            ax.set_xlabel("날짜")
            ax.set_ylabel("판매량")
            ax.legend()
            ax.grid(True)
            fig.tight_layout()

            st.pyplot(fig)
            plt.close(fig)

            # 저장 경로 설정 및 디렉토리 생성
            save_path = f"images/result/{plant_name} LSTM 공장별 판매량 예측_{forecast_months}개월.png"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig.savefig(save_path, dpi=300)

            # 세션 스테이트에 저장
            st.session_state["last_forecast_image"] = save_path

            st.success(f"📊 그래프가 저장되었습니다: `{save_path}`")

        # 5. 실행 예시
        file_path = "data/processed/hyundai-by-plant.csv"
        df = pd.read_csv(file_path)

        # 전처리: 인덱스 통합
        df['공장명(국가)'] = df['공장명(국가)'].astype(str) + '-' + df['차종'].astype(str).str.zfill(2) + '-' + df['거래 구분'].astype(str).str.zfill(2)
        df = df.drop(columns=['차종', '거래 구분'])
        cols = ['공장명(국가)'] + [col for col in df.columns if col != '공장명(국가)']
        df = df[cols]

        plant_list = ["선택하세요"] + list(set([x.split("-")[0] for x in df['공장명(국가)'].unique()]))
        if "CKD (모듈형 조립 방식)" in plant_list:
            plant_list.remove("CKD (모듈형 조립 방식)")
        car_list = ["선택하세요"] + list(set([x.split("-")[1] for x in df['공장명(국가)'].unique()]))
        range_list = ["선택하세요"] + list(set([x.split("-")[2] for x in df['공장명(국가)'].unique()]))
        plant_name = st.selectbox("공장을 선택하세요.", plant_list, key="plant_list") + "-" + st.selectbox("차종을 선택하세요.", car_list, key="plant_car_list") + "-" + st.selectbox("거래 구분을 선택하세요.", range_list, key="plant_range_list")
        forecast_months = st.number_input("몇 개월 뒤까지 예측할까요?", min_value=1, max_value=24, value=12, key="plant_month")

        if st.button("공장별 판매량 예측 시작") :
            if "선택하세요" in plant_name:
                st.error("공장, 차종, 거래 구분을 선택해주세요.")
            else:
                plant_data = df[df['공장명(국가)'] == plant_name].iloc[:, 1:].T
                if plant_data.empty:
                    st.error("선택한 조건에 대한 데이터가 없습니다.")
                else:
                    plant_data.columns = ['y']
                    plant_data.index = pd.to_datetime(plant_data.index)
                    plant_data = plant_data.asfreq('MS')
                    plant_data['y'] = pd.to_numeric(plant_data['y'], errors='coerce')
                    plant_data = plant_data.dropna()

                    def get_model_path(plant_name):
                        return f"models/lstm_plant_{plant_name}_model.h5"

                    def get_scaler_path(plant_name):
                        return f"models/lstm_plant_{plant_name}_scaler.pkl"

                    def ensure_model(plant_name):
                        model_path = get_model_path(plant_name)
                        scaler_path = get_scaler_path(plant_name)

                        if os.path.exists(model_path) and os.path.exists(scaler_path):
                            print(f"✅ 저장된 모델과 스케일러가 존재합니다: {model_path}")
                            return True
                        else:
                            print(f"🚀 모델 또는 스케일러가 존재하지 않아 새로 학습합니다.")
                            return False

                    status = ensure_model(plant_name)

                    # ✅ 특정 기간 값이 모두 0인지 확인
                    zero_check_range = plant_data.loc["2024-09":"2025-02", "y"]
                    if zero_check_range.sum() == 0:
                        st.error("🚫 이 차는 더 이상 생산하지 않습니다.")
                    else :
                        if status:
                            lstm_model = load_model(get_model_path(plant_name), compile=False)
                            scaler = joblib.load(get_scaler_path(plant_name))
                        else:
                            st.info("생성된 모델이 존재하지 않아 모델 생성을 시작합니다.")
                            st.info("30초 이상 소요될 수 있습니다.")
                            with st.spinner("🔄 모델을 학습 중입니다... 잠시만 기다려주세요."):
                                X, y, scaler = prepare_lstm_data(plant_data)
                                lstm_model = train_lstm_model(X, y, plant_name=plant_name)
                                # 모델이 조기 종료되지 않은 경우에만 여기서 저장
                                if not os.path.exists(get_model_path(plant_name)):
                                    lstm_model.save(get_model_path(plant_name))
                                    joblib.dump(scaler, get_scaler_path(plant_name))

                        lstm_forecast = forecast_lstm(lstm_model, plant_data, forecast_months, scaler)
                        plot_lstm_forecast(plant_data, lstm_forecast, plant_name, forecast_months)