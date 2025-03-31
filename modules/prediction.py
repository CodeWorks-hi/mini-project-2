import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import Input, Dense, LSTM
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import platform
import os
import joblib
from sklearn.metrics import r2_score
import matplotlib.dates as mdates
import io
import joblib
import matplotlib.pyplot as plt
import time

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


def send_predictions_to_recommendations(predictions):
    st.session_state.predictions = predictions

def prediction_ui():
    st.title("AI 판매 예측 시스템")
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
            return np.array(X), np.array(y), scaler

        # 1-2. 모델 정의 및 학습
        def train_lstm_model(X, y, units=50, epochs=600, batch_size=16, region_name=None):
            input_shape = (X.shape[1], X.shape[2])
            model = Sequential([
                Input(shape=input_shape),
                LSTM(units=units, activation='relu'),
                Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse')
            
            # 조기 종료를 위한 콜백 클래스 정의
            class EarlyStoppingByLoss(tf.keras.callbacks.Callback):
                def __init__(self, region_name):
                    super(EarlyStoppingByLoss, self).__init__()
                    self.region_name = region_name
                    
                def on_epoch_end(self, epoch, logs=None):
                    current_loss = logs.get('loss')
                    if current_loss is not None and current_loss <= 0.01:
                        print(f"\n조기 종료: epoch {epoch+1}에서 loss가 0.01 이하({current_loss:.4f})로 떨어짐")
                        # 모델 저장
                        model_path = get_model_path(self.region_name)
                        scaler_path = get_scaler_path(self.region_name)
                        self.model.save(model_path)
                        print(f"모델이 {model_path}에 저장되었습니다.")
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
            losses = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            loss_chart = st.empty()


            for epoch in range(epochs):
                history = model.fit(X, y, epochs=1, batch_size=batch_size, verbose=0)
                loss = history.history['loss'][0]
                losses.append(loss)
                
                if epoch % 10 == 0 or epoch == epochs - 1:
                    progress = (epoch + 1) / epochs
                    progress_bar.progress(progress)
                    status_text.text(f"Epoch {epoch+1}/{epochs} - loss: {loss:.4f}")
    
                time.sleep(0.1)  # 애니메이션 효과를 위한 짧은 대기 시간

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

            fig1, ax = plt.subplots(figsize=(12, 6))
            ax.plot(series.index, series['y'], label='실제 수출량', color='black')
            ax.plot(forecast_index, forecast_values, label='LSTM 예측', color='red', linestyle='--')
            ax.axvline(x=series.index[-1], color='gray', linestyle=':', label='예측 시작점')
            ax.set_title(f"{region_name} LSTM 기반 수출량 예측")
            ax.set_xlabel("날짜")
            ax.set_ylabel("수출량")
            ax.legend()
            ax.grid(True)
            fig1.tight_layout()

            st.pyplot(fig1)
            plt.close(fig1)

            # 저장 경로 생성
            save_path = f"images/result/{region_name} LSTM 지역별 수출량 예측.png"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig1.savefig(save_path, dpi=300)

            return save_path

        def add_download_button(forecast_df, region_name, filename="lstm_forecast.csv"):
            csv = forecast_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="예측 결과 CSV 다운로드",
                data=csv,
                file_name=f"{region_name}_{filename}",
                mime='text/csv'
            )
        
        def display_lstm_forecast_table(forecast_df, region_name):
            forecast_df = forecast_df.copy()
            forecast_df['연도'] = forecast_df['연도'].astype(int)
            forecast_df['월'] = forecast_df['월'].astype(int)
            forecast_df['예측 수출량'] = forecast_df['예측 수출량'].round()

            # 증감률(%) 계산 및 포맷 처리
            pct_change = forecast_df['예측 수출량'].pct_change() * 100
            pct_change = pct_change.round(2)
            forecast_df['전월 대비 증감률(%)'] = pct_change.apply(lambda x: f"{x:.2f}" if pd.notnull(x) else '-')
            
            st.subheader("예측 결과 표 (LSTM 기반)")
            col1, col2 = st.columns([1, 0.9])
            with col1:
                st.dataframe(forecast_df, use_container_width=True, hide_index=True)
                filename = "LSTM_수출예측.csv"
                add_download_button(forecast_df, region_name, filename)
            with col2:
                img_path = plot_lstm_forecast(region_data, lstm_forecast, region_name, forecast_months)
                if os.path.exists(img_path):
                    with open(img_path, "rb") as img_file:
                        st.download_button(
                            label="예측 그래프 이미지 다운로드",
                            data=img_file,
                            file_name=f"{region_name}_LSTM_예측.png",
                            mime="image/png"
                        )

        # 모델 및 스케일러 경로 함수
        def get_model_path(region_name):
            return f"models/lstm_region_{region_name}_model.h5"

        def get_scaler_path(region_name):
            return f"models/lstm_region_{region_name}_scaler.pkl"

        def ensure_model(region_name):
            model_path = get_model_path(region_name)
            scaler_path = get_scaler_path(region_name)

            if os.path.exists(model_path) and os.path.exists(scaler_path):
                print(f"저장된 모델과 스케일러가 존재합니다: {model_path}")
                return True
            else:
                print(f"모델 또는 스케일러가 존재하지 않아 새로 학습합니다.")
                return False

        # 1. 지역별 수출량 예측
        file_path = "data/processed/hyundai-by-region.csv"  # 현대만 할 거니까~
        df = pd.read_csv(file_path)

        with st.expander("원본 데이터 확인") :
            st.dataframe(df)

        region_list = ["선택하세요"] + sorted(df['지역명'].unique())
        region_list.remove("서유럽")
        region_list.remove("동유럽")
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
                region_data.index = pd.to_datetime(region_data.index, format='%Y-%m', errors='coerce')
                region_data = region_data.asfreq('MS')
                region_data['y'] = pd.to_numeric(region_data['y'], errors='coerce')
                region_data = region_data.dropna()

                status = ensure_model(region_name)

                if status:
                    lstm_model = load_model(get_model_path(region_name), compile=False)
                    scaler = joblib.load(get_scaler_path(region_name))
                else:
                    st.info("모델생성을 새로 시작중입니다. 모델생성이 1분 이상 소요될 수 있습니다")
                    with st.spinner("모델을 학습 중입니다... 잠시만 기다려주세요."):
                        X, y, scaler = prepare_lstm_data(region_data)
                        lstm_model = train_lstm_model(X, y, region_name=region_name)
                        joblib.dump(scaler, get_scaler_path(region_name))
                        # 모델이 조기 종료되지 않은 경우에만 여기서 저장
                        if not os.path.exists(get_model_path(region_name)):
                            lstm_model.save(get_model_path(region_name))

                lstm_forecast = forecast_lstm(lstm_model, region_data, forecast_months, scaler)
                send_predictions_to_recommendations({"type": "region","name": region_name,"forecast": lstm_forecast.to_dict()})
                # plot_lstm_forecast(region_data, lstm_forecast, region_name, forecast_months)
                display_lstm_forecast_table(lstm_forecast, region_name)
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
            input_shape = (X.shape[1], X.shape[2])
            model = Sequential([
                Input(shape=input_shape),
                LSTM(units=units, activation='relu'),
                Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse')
            
            # 조기 종료를 위한 콜백 클래스 정의
            class EarlyStoppingByLoss(tf.keras.callbacks.Callback):
                def __init__(self, car_name):
                    super(EarlyStoppingByLoss, self).__init__()
                    self.car_name = car_name
                    
                def on_epoch_end(self, epoch, logs=None):
                    current_loss = logs.get('loss')
                    if current_loss is not None and current_loss <= 0.01:
                        print(f"\n조기 종료: epoch {epoch+1}에서 loss가 0.01 이하({current_loss:.4f})로 떨어짐")
                        # 모델 저장
                        model_path = get_model_path(self.car_name)
                        scaler_path = get_scaler_path(self.car_name)
                        self.model.save(model_path)
                        print(f"모델이 {model_path}에 저장되었습니다.")
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
            losses = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            loss_chart = st.empty()


            for epoch in range(epochs):
                history = model.fit(X, y, epochs=1, batch_size=batch_size, verbose=0)
                loss = history.history['loss'][0]
                losses.append(loss)
                
                if epoch % 10 == 0 or epoch == epochs - 1:
                    progress = (epoch + 1) / epochs
                    progress_bar.progress(progress)
                    status_text.text(f"Epoch {epoch+1}/{epochs} - loss: {loss:.4f}")
    
                time.sleep(0.1)  # 애니메이션 효과를 위한 짧은 대기 시간

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

            fig2, ax = plt.subplots(figsize=(12, 6))
            ax.plot(series.index, series['y'], label='실제 판매량', color='black')
            ax.plot(forecast_index, forecast_values, label='LSTM 예측', color='red', linestyle='--')
            ax.axvline(x=series.index[-1], color='gray', linestyle=':', label='예측 시작점')
            ax.set_title(f"{car_name} LSTM 기반 판매량 예측")
            ax.set_xlabel("날짜")
            ax.set_ylabel("판매량")
            ax.legend()
            ax.grid(True)
            fig2.tight_layout()

            st.pyplot(fig2)
            plt.close(fig2)

            # 저장 경로 생성
            save_path = f"images/result/{car_name} LSTM 지역별 수출량 예측.png"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig2.savefig(save_path, dpi=300)

            return save_path

        def add_download_button(forecast_df, car_name, filename="lstm_forecast.csv"):
            csv = forecast_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="예측 결과 CSV 다운로드",
                data=csv,
                file_name=f"{car_name}_{filename}",
                mime='text/csv'
            )
        
        def display_lstm_forecast_table(forecast_df, car_name):
            forecast_df = forecast_df.copy()
            forecast_df['연도'] = forecast_df['연도'].astype(int)
            forecast_df['월'] = forecast_df['월'].astype(int)
            forecast_df['예측 판매량'] = forecast_df['예측 판매량'].round()

            # 증감률(%) 계산 및 포맷 처리
            pct_change = forecast_df['예측 판매량'].pct_change() * 100
            pct_change = pct_change.round(2)
            forecast_df['전월 대비 증감률(%)'] = pct_change.apply(lambda x: f"{x:.2f}" if pd.notnull(x) else '-')
            
            st.subheader("예측 결과 표 (LSTM 기반)")
            col1, col2 = st.columns([1, 0.9])
            with col1:
                st.dataframe(forecast_df, use_container_width=True, hide_index=True)
                filename = "LSTM_판매예측.csv"
                add_download_button(forecast_df, car_name, filename)
            with col2:
                img_path = plot_lstm_forecast(car_data, lstm_forecast, car_name, forecast_months)
                if os.path.exists(img_path):
                    with open(img_path, "rb") as img_file:
                        st.download_button(
                            label="예측 그래프 이미지 다운로드",
                            data=img_file,
                            file_name=f"{car_name}_LSTM_예측.png",
                            mime="image/png"
                        )

        # 5. 실행 예시
        file_path = "data/processed/hyundai-by-car.csv"
        df = pd.read_csv(file_path)

        with st.expander("원본 데이터 확인") :
            st.dataframe(df)

        # 전처리: 인덱스 통합
        df['차종'] = df['차종'].astype(str) + '-' + df['거래 구분'].astype(str).str.zfill(2)
        df = df.drop(columns=['차량 유형', '거래 구분'])
        cols = ['차종'] + [col for col in df.columns if col != '차종']
        df = df[cols]

        car_list = ["선택하세요"] + sorted(set([x.split("-")[0] for x in df['차종'].unique()]))
        car_selection = st.selectbox("차종을 선택하세요.", car_list, key="car_list")
        if car_selection != "선택하세요":
            filtered_ranges = sorted(set(x.split("-")[1] for x in df['차종'].unique() if x.startswith(car_selection + "-")))
            range_list = ["선택하세요"] + filtered_ranges
        else:
            range_list = ["선택하세요"]
        range_selection = st.selectbox("거래 구분을 선택하세요.", range_list, key="range_list")
        car_name = car_selection + "-" + range_selection
        forecast_months = st.number_input("몇 개월 뒤까지 예측할까요?", min_value=1, max_value=24, value=12, key="car_month")

        if st.button("차종별 판매량 예측 시작") :
            if "선택하세요" in car_name :
                st.error("차종과 거래 구분을 선택해주세요.")
            else:   
                car_data = df[df['차종'] == car_name].iloc[:, 1:].T
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
                        print(f"저장된 모델과 스케일러가 존재합니다: {model_path}")
                        return True
                    else:
                        print(f" 모델 또는 스케일러가 존재하지 않아 새로 학습합니다.")
                        return False

                status = ensure_model(car_name)

                # ✅ 특정 기간 값이 모두 0인지 확인
                zero_check_range = car_data.loc["2024-09":"2025-02", "y"]
                if zero_check_range.sum() == 0:
                    st.error(" 이 차는 더 이상 생산하지 않습니다.")
                    st.stop
                else :
                    if status:
                        lstm_model = load_model(get_model_path(car_name), compile=False)
                        scaler = joblib.load(get_scaler_path(car_name))
                    else:
                        st.info("모델생성을 새로 시작중입니다. 모델생성이 1분 이상 소요될 수 있습니다")
                        with st.spinner("모델을 학습 중입니다... 잠시만 기다려주세요."):
                            X, y, scaler = prepare_lstm_data(car_data)
                            lstm_model = train_lstm_model(X, y, car_name=car_name)
                            joblib.dump(scaler, get_scaler_path(car_name))
                            # 모델이 조기 종료되지 않은 경우에만 여기서 저장
                            if not os.path.exists(get_model_path(car_name)):
                                lstm_model.save(get_model_path(car_name))

                    lstm_forecast = forecast_lstm(lstm_model, car_data, forecast_months, scaler)
                    send_predictions_to_recommendations({ "type": "car","name": car_name,"forecast": lstm_forecast.to_dict()})
                    # plot_lstm_forecast(car_data, lstm_forecast, car_name, forecast_months)
                    display_lstm_forecast_table(lstm_forecast, car_name)
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
            input_shape = (X.shape[1], X.shape[2])
            model = Sequential([
                Input(shape=input_shape),
                LSTM(units=units, activation='relu'),
                Dense(1)
            ])
            model.compile(optimizer='adam', loss='mse')
            
            # 조기 종료를 위한 콜백 클래스 정의
            class EarlyStoppingByLoss(tf.keras.callbacks.Callback):
                def __init__(self, plant_name):
                    super(EarlyStoppingByLoss, self).__init__()
                    self.plant_name = plant_name
                    
                def on_epoch_end(self, epoch, logs=None):
                    current_loss = logs.get('loss')
                    if current_loss is not None and current_loss <= 0.01:
                        print(f"\n조기 종료: epoch {epoch+1}에서 loss가 0.01 이하({current_loss:.4f})로 떨어짐")
                        # 모델 저장
                        model_path = get_model_path(self.plant_name)
                        scaler_path = get_scaler_path(self.plant_name)
                        self.model.save(model_path)
                        print(f"모델이 {model_path}에 저장되었습니다.")
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
            losses = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            loss_chart = st.empty()


            for epoch in range(epochs):
                history = model.fit(X, y, epochs=1, batch_size=batch_size, verbose=0)
                loss = history.history['loss'][0]
                losses.append(loss)
                
                if epoch % 10 == 0 or epoch == epochs - 1:
                    progress = (epoch + 1) / epochs
                    progress_bar.progress(progress)
                    status_text.text(f"Epoch {epoch+1}/{epochs} - loss: {loss:.4f}")
    
                time.sleep(0.1)  # 애니메이션 효과를 위한 짧은 대기 시간

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
        def plot_lstm_forecast(series, forecast_df, plant_name, save_path=None):
            forecast_index = pd.to_datetime(forecast_df['연도'].astype(str) + '-' + forecast_df['월'].astype(str))
            forecast_values = forecast_df['예측 판매량'].values

            fig3, ax = plt.subplots(figsize=(12, 6))
            ax.plot(series.index, series['y'], label='실제 판매량', color='black')
            ax.plot(forecast_index, forecast_values, label='LSTM 예측', color='red', linestyle='--')
            ax.axvline(x=series.index[-1], color='gray', linestyle=':', label='예측 시작점')
            ax.set_title(f"{plant_name} LSTM 기반 판매량 예측")
            ax.set_xlabel("날짜")
            ax.set_ylabel("판매량")
            ax.legend()
            ax.grid(True)
            fig3.tight_layout()

            st.pyplot(fig3)
            plt.close(fig3)

            # 저장 경로 설정 및 디렉토리 생성
            save_path = f"images/result/{plant_name} LSTM 공장별 판매량 예측.png"
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            fig3.savefig(save_path, dpi=300)

            return save_path

        def add_download_button(forecast_df, plant_name, filename="lstm_forecast.csv"):
            csv = forecast_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="예측 결과 CSV 다운로드",
                data=csv,
                file_name=f"{plant_name}_{filename}",
                mime='text/csv'
            )
        
        def display_lstm_forecast_table(forecast_df, plant_name):
            forecast_df = forecast_df.copy()
            forecast_df['연도'] = forecast_df['연도'].astype(int)
            forecast_df['월'] = forecast_df['월'].astype(int)
            forecast_df['예측 판매량'] = forecast_df['예측 판매량'].round()

            # 증감률(%) 계산 및 포맷 처리
            pct_change = forecast_df['예측 판매량'].pct_change() * 100
            pct_change = pct_change.round(2)
            forecast_df['전월 대비 증감률(%)'] = pct_change.apply(lambda x: f"{x:.2f}" if pd.notnull(x) else '-')

            st.subheader("예측 결과 표 (LSTM 기반)")
            col1, col2 = st.columns([1, 0.9])
            with col1:
                st.dataframe(forecast_df, use_container_width=True, hide_index=True)
                filename = "LSTM_판매예측.csv"
                add_download_button(forecast_df, plant_name, filename)
            with col2:
                img_path = plot_lstm_forecast(plant_data, lstm_forecast, plant_name, forecast_months)
                if os.path.exists(img_path):
                    with open(img_path, "rb") as img_file:
                        st.download_button(
                            label="예측 그래프 이미지 다운로드",
                            data=img_file,
                            file_name=f"{plant_name}_LSTM_예측.png",
                            mime="image/png"
                        )

        # 5. 실행 예시
        file_path = "data/processed/hyundai-by-plant.csv"
        df = pd.read_csv(file_path)

        with st.expander("원본 데이터 확인") :
            st.dataframe(df)

        # 전처리: 인덱스 통합
        df['공장명(국가)'] = df['공장명(국가)'].astype(str) + '-' + df['차종'].astype(str).str.zfill(2) + '-' + df['거래 구분'].astype(str).str.zfill(2)
        df = df.drop(columns=['차종', '거래 구분'])
        cols = ['공장명(국가)'] + [col for col in df.columns if col != '공장명(국가)']
        df = df[cols]

        plant_raw = df['공장명(국가)'].unique()
        plant_list = sorted(set(x.split("-")[0] for x in plant_raw if not x.startswith(("CKD", "기타")))) + ["기타"]
        car_by_plant = {plant: set() for plant in plant_list}
        range_by_plant_car = {}

        for full in plant_raw:
            parts = full.split("-")
            if len(parts) == 3 and not parts[0].startswith("CKD"):
                plant, car, rng = parts
                car_by_plant[plant].add(car)
                range_by_plant_car[(plant, car)] = range_by_plant_car.get((plant, car), set())
                range_by_plant_car[(plant, car)].add(rng)
        
        plant_list = ["선택하세요"] + plant_list
        plant_selection = st.selectbox("공장을 선택하세요.", plant_list, key="plant_list")

        if plant_selection != "선택하세요":
            cars = sorted(car_by_plant.get(plant_selection, []))
            car_list = ["선택하세요"] + cars
        else:
            car_list = ["선택하세요"]
        car_selection = st.selectbox("차종을 선택하세요.", car_list, key="plant_car_list")

        if plant_selection != "선택하세요" and car_selection != "선택하세요":
            ranges = sorted(range_by_plant_car.get((plant_selection, car_selection), []))
            range_list = ["선택하세요"] + ranges
        else:
            range_list = ["선택하세요"]
        range_selection = st.selectbox("거래 구분을 선택하세요.", range_list, key="plant_range_list")

        # 최종 조합
        if plant_selection != "선택하세요" and car_selection != "선택하세요" and range_selection != "선택하세요":
            plant_name = f"{plant_selection}-{car_selection}-{range_selection}"

        forecast_months = st.number_input("몇 개월 뒤까지 예측할까요?", min_value=1, max_value=24, value=12, key="plant_month")

        if st.button("공장별 판매량 예측 시작") :
            if "선택하세요" in plant_name:
                st.error("공장, 차종, 거래 구분을 선택해주세요.")
            else:
                plant_data = df[df['공장명(국가)'] == plant_name].iloc[:, 1:].T
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
                        print(f"저장된 모델과 스케일러가 존재합니다: {model_path}")
                        return True
                    else:
                        print(f"모델 또는 스케일러가 존재하지 않아 새로 학습합니다.")
                        return False

                status = ensure_model(plant_name)

                # ✅ 특정 기간 값이 모두 0인지 확인
                zero_check_range = plant_data.loc["2024-09":"2025-02", "y"]
                if zero_check_range.sum() == 0:
                    st.error("이 차는 더 이상 생산하지 않습니다.")
                    st.stop
                else :
                    if status:
                        lstm_model = load_model(get_model_path(plant_name), compile=False)
                        scaler = joblib.load(get_scaler_path(plant_name))
                    else:
                        st.info("모델생성을 새로 시작중입니다. 모델생성이 1분 이상 소요될 수 있습니다")
                        with st.spinner("모델을 학습 중입니다... 잠시만 기다려주세요."):
                            X, y, scaler = prepare_lstm_data(plant_data)
                            lstm_model = train_lstm_model(X, y, plant_name=plant_name)
                            joblib.dump(scaler, get_scaler_path(plant_name))
                            # 모델이 조기 종료되지 않은 경우에만 여기서 저장
                            if not os.path.exists(get_model_path(plant_name)):
                                lstm_model.save(get_model_path(plant_name))
                                

                    lstm_forecast = forecast_lstm(lstm_model, plant_data, forecast_months, scaler)
                    send_predictions_to_recommendations({"type": "plant","name": plant_name,"forecast": lstm_forecast.to_dict()})
                    # plot_lstm_forecast(plant_data, lstm_forecast, plant_name, forecast_months)
                    display_lstm_forecast_table(lstm_forecast, plant_name)